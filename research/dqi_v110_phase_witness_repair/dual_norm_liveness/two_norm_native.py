"""Conditional 84-CCX XOR accumulate. A/B norm registers must already be live."""
import hashlib,json,random
from pathlib import Path
import kickmix as km
import numpy as np
from rank42 import CODES

K=2048
def mul(a,b):
    r=0
    while b:
        if b&1:r^=a
        b>>=1
        a<<=1
        if a>>12:a^=0x1053
    return r
def sq(x):return mul(x,x)
z=K;tr=0
for j in range(12):tr^=z;z=sq(z)
assert tr==1
def norm(a,b):return sq(a)^mul(a,b)^mul(K,sq(b))
def ref(a,b,c,d):
    m=mul(b,d)
    return mul(a,c)^mul(K,m),mul(a,d)^mul(b,c)^m
def parity(x):return x.bit_count()&1
def indices(mask):
    while mask:
        q=mask&-mask;mask^=q;yield q.bit_length()-1

# 0..47 operands, 48..71 supplied norms, 72..95 arbitrary dirty target.
A0,A1,B0,B1,NA,NB,O0,O1=[list(range(i,i+12)) for i in range(0,96,12)]
ops=[]
def cx(a,b):ops.append(('CX',a,b))
def swap(a,b):ops.append(('SWAP',a,b))
def ccx(a,b,t):ops.append(('CCX',a,b,t))
def addmap(src,dst,fun):
    for j,a in enumerate(src):
        for k in indices(fun(1<<j)):cx(a,dst[k])
def linear_frame(wires,cols):
    rows=[sum(((c>>i)&1)<<j for j,c in enumerate(cols)) for i in range(len(cols))]
    el=[]
    for j,n in enumerate(wires):
        piv=next(i for i in range(j,len(cols)) if rows[i]>>j&1)
        if j!=piv:
            rows[j],rows[piv]=rows[piv],rows[j]
            el.append(('SWAP',wires[j],wires[piv]))
        for i in range(len(cols)):
            if i!=j and rows[i]>>j&1:
                rows[i]^=rows[j]
                el.append(('CX',n,wires[i]))
    assert rows==[1<<i for i in range(len(cols))]
    ops.extend(reversed(el))
def field_product(a,b,c):
    w=a+b+c
    for k in CODES:
        i,j=k%64,(k//64)%64
        if k<4096:cx(w[i],w[j])
        else:ccx(w[i],w[j],w[k//4096-1])
def addnorm(tgt):
    addmap(A0,tgt,sq)
    addmap(A1,tgt,lambda x:mul(K,sq(x)))
    field_product(A0,A1,tgt)
def add_conj_b():
    addmap(B0,A0,lambda x:x)
    addmap(B1,A0,lambda x:x)
    addmap(B1,A1,lambda x:x)
def map_theta_cols(x):
    a=x&4095;b=x>>12
    return mul(K,b)|((a^b)<<12)

add_conj_b()
addmap(O1,O0,lambda x:x)
addnorm(O1)
addmap(O1,O0,lambda x:x)
add_conj_b()
s=len(ops)
linear_frame(A0+A1,[map_theta_cols(1<<i) for i in range(24)])
r=len(ops)
add_conj_b()
addnorm(O0)
add_conj_b()
ops.extend(reversed(ops[s:r]))
addmap(NA,O0,lambda x:mul(K^1,x))
addmap(NA,O1,lambda x:x)
addmap(NB,O1,lambda x:x)

# Gate-level squarefree GF(2) ANF, substituting the stated norm ABI.
def pol(x,y):
    q=set()
    for u in x:
        for v in y:
            m=u|v
            if m in q:q.remove(m)
            else:q.add(m)
    return q
def basis_poly(a,b,fn):
    out=[set() for _ in range(12)]
    for i,x in enumerate(a+b):
        mask=fn((1<<i)&4095,(1<<i)>>12)
        for k in indices(mask):out[k].add(1<<x)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            for k in indices(mul(1<<i,1<<j)):out[k].add((1<<x)|(1<<y))
    return out
terms=[{1<<i} for i in range(96)]
for a,b,ns in ((A0,A1,NA),(B0,B1,NB)):
    for s,v in zip(ns,basis_poly(a,b,norm)):terms[s]=v
entry=[t.copy() for t in terms]
for op,a,b,*extra in ops:
    if op=='CX':terms[b]^=terms[a]
    if op=='SWAP':terms[a],terms[b]=terms[b],terms[a]
    if op=='CCX':terms[extra[0]]^=pol(terms[a],terms[b])
assert all(terms[i]==entry[i] for i in range(72))
expected=[set() for _ in range(24)]
for i,a in enumerate(A0+A1):
    u=1<<i
    for j,b in enumerate(B0+B1):
        v=1<<j
        x,y=ref(u&4095,u>>12,v&4095,v>>12)
        for k in indices(x|(y<<12)):expected[k].add((1<<a)|(1<<b))
assert all(terms[k]^entry[k]==e for k,e in zip(O0+O1,expected))

p=Path(__file__).with_name('two_norm_84.kmb')
c=km.Circuit('\n'.join(op+' '+' '.join(f'q{q}' for q in args) for op,*args in ops))
c.to_file(str(p),format='kmb');c=km.Circuit.from_file(str(p))
assert c.num_qubits==96 and int(c.operation_statistics().num_toffoli_like)==84
g=random.Random(137621)
qq=[km.q(i) for i in range(96)]
def unpack(words):
    return ((np.array(words,np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(words),96).T.astype(bool)
for i in range(0,8192,128):
    X=[];Y=[]
    for j in range(128):
        a,b,c0,d,e,f=[g.randrange(4096) for _ in range(6)]
        x=(a,b,c0,d,norm(a,b),norm(c0,d),e,f)
        u,v=ref(a,b,c0,d)
        X.append(x);Y.append(x[:6]+(e^u,f^v))
    s=km.Simulator(batch_size=128,seed=12345+i)
    s.write_across_shots(qq,unpack(X));s.do(c)
    assert np.array_equal(s.read_across_shots(qq),unpack(Y))
    assert not s.read_phase_flipped_across_shots().any()
    s.do(c)
    assert np.array_equal(s.read_across_shots(qq),unpack(X))
    assert not s.read_phase_flipped_across_shots().any()
print(json.dumps(dict(Q=c.num_qubits,CCX=int(c.operation_statistics().num_toffoli_like),ops=len(c),exact_anf=True,forward_inverse=8192,sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
