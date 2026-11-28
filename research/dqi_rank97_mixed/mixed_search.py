"""Quadratic (not necessarily bilinear) search and native dirty-target compiler.
Inputs are the exact two normalized tensors from #311/#316.
No syndrome, sample, or salt affects synthesis. A full-tape splice is separate.
"""
from pathlib import Path
import base64, zlib, random, json, hashlib, sys
D=Path(__file__).parent
def decode(name):
    raw=zlib.decompress(base64.b64decode((D/name).read_text()))
    assert len(raw)%891==0
    ns=[int.from_bytes(raw[i:i+3],'little') for i in range(0,len(raw),3)]
    return [list(zip(ns[i:i+297:3],ns[i+1:i+297:3],ns[i+2:i+297:3])) for i in range(0,len(ns),297)]
T=decode('terms4.b64'); U=decode('terms8.b64')
sources=[[T[0],T[1],U[0]],[T[2],T[3],U[1]]]
def bits(x):
    while x:
        l=x&-x;yield l.bit_length()-1;x^=l
def plane(a,b,c):
    if not a or not b or a==b or not c:return None
    s=sorted((a,b,a^b))
    return s[0],s[1],c
def polar(ts):
    q={}
    for a,b,c in ts:
        for i in bits(a):
            for j in bits(b):
                if i!=j:
                    k=min(i,j),max(i,j);q[k]=q.get(k,0)^c
    return {k:v for k,v in q.items() if v}
def linear(ts):
    q={}
    for a,b,c in ts:
        for i in bits(a&b):q[i]=q.get(i,0)^c
    return {k:v for k,v in q.items() if v}
def merge(ts):
    q={}
    for t in ts:
        if t:
            a,b,c=t;q[a,b]=q.get((a,b),0)^c
    return [(a,b,c) for (a,b),c in q.items() if c]
def has(t,p):return p in (t[0],t[1],t[0]^t[1])
def other(t,p):return t[1] if t[0]==p else t[0]
def factor_common(ts,p):
    ind=[i for i,t in enumerate(ts) if has(t,p)]
    if len(ind)<2:return ts
    pivot=1<<(p.bit_length()-1);B={}
    for i in ind:
        v=other(ts[i],p);v^=p if v&pivot else 0;c=ts[i][2]
        while v:
            j=v.bit_length()-1
            if j in B:
                w,d=B[j];v^=w;B[j]=(w,d^c)
            else:
                B[j]=(v,c);break
    out=[plane(p,v,c) for v,c in B.values() if c]
    if len(out)>=len(ind):return ts
    return merge([t for i,t in enumerate(ts) if i not in ind]+out)
def factor_output(ts,c,n=48):
    ind=[i for i,t in enumerate(ts) if t[2]==c]
    if len(ind)<2:return ts
    A=[0]*n
    for i in ind:
        a,b,_=ts[i]
        for k in bits(a):A[k]^=b
        for k in bits(b):A[k]^=a
    out=[]
    while any(A):
        i=next(k for k in range(n) if A[k]);j=A[i].bit_length()-1
        a,b=A[j],A[i];out.append(plane(a,b,c))
        for k in bits(a):A[k]^=b
        for k in bits(b):A[k]^=a
    if len(out)>=len(ind):return ts
    return merge([t for i,t in enumerate(ts) if i not in ind]+out)
def search(initial,seed,steps):
    rng=random.Random(seed);ts=list(initial);best=list(initial);goal=polar(initial)
    def basis(t):return rng.sample([t[0],t[1],t[0]^t[1]],2)
    for i in range(steps):
        cap=110 if i<steps*0.4 else 104 if i<steps*0.85 else 101
        j=rng.randrange(len(ts));t=ts[j];p=rng.choice([t[0],t[1],t[0]^t[1]])
        a=rng.randrange(20)
        if a<2:
            c=factor_common(ts,p)
        elif a==2:
            c=factor_output(ts,t[2])
        else:
            choices=[]
            for k,u in enumerate(ts):
                if k==j:continue
                if u[2]==t[2]:choices.append((k,0))
                h=next((h for h in (t[0],t[1],t[0]^t[1]) if has(u,h)),0)
                if h:choices.append((k,h))
            if choices and (len(ts)>=cap or rng.randrange(10)):
                k,h=rng.choice(choices);u=ts[k]
                if h:
                    x,y=other(t,h),other(u,h)
                    changes=[plane(h,x^y,t[2]),plane(h,y,u[2]^t[2])]
                else:
                    x,y=basis(t);z,w=basis(u)
                    changes=[plane(x,y^w,t[2]),plane(x^z,w,t[2])]
                c=merge([q for k2,q in enumerate(ts) if k2 not in (j,k)]+changes)
            elif len(ts)<cap:
                x,y=basis(t);z=rng.choice(basis(rng.choice(ts)))
                c=merge(ts[:j]+ts[j+1:]+[plane(x,y^z,t[2]),plane(x,z,t[2])])
            else:c=ts
        if len(c)<=cap:ts=c
        elif i%100==0:ts=list(initial)
        if len(ts)<len(best):
            assert polar(ts)==goal
            best=list(ts)
            if len(best)<=97:break
    assert polar(best)==goal
    return best
def reference(ts,x,y):
    v=0
    for a,b,c in ts:
        if (a&x).bit_count()%2 and (b&y).bit_count()%2:v^=c
    return v
def evaluate(ts,x):
    v=0
    for a,b,c in ts:
        if (a&x).bit_count()%2 and (b&x).bit_count()%2:v^=c
    for i,c in linear(ts).items():
        if (x>>i)&1:v^=c
    return v
def build(ts,ni,no):
    import kickmix as km
    cb=km.CircuitBuilder();cb.set_max_qubits(ni+no);q=list(cb.create_quantum_register(ni+no,'W'))
    for i,c in linear(ts).items():
        for j in bits(c):cb.cx(q[i],q[ni+j])
    for a,b,c in ts:
        pre=[];p=next(bits(a))
        for i in bits(a^(1<<p)):pre.append((i,p))
        v=b
        if b&(1<<p):v^=a^(1<<p)
        j=next(i for i in bits(v) if i!=p)
        for i in bits(v^(1<<j)):pre.append((i,j))
        for i,k in pre:cb.cx(q[i],q[k])
        t=ni+next(bits(c));dirs=[ni+i for i in bits(c) if ni+i!=t]
        for i in dirs:cb.cx(q[t],q[i])
        cb.ccx(q[p],q[j],q[t])
        for i in reversed(dirs):cb.cx(q[t],q[i])
        for i,k in reversed(pre):cb.cx(q[i],q[k])
    return cb.finish_circuit()
def native(ts,inputs,expected,ni,no,name):
    import kickmix as km,numpy as np
    c=build(ts,ni,no);path=D/(name+'.kmb');c.to_file(str(path),format='kmb')
    c=km.Circuit.from_file(str(path))
    assert c.num_qubits==ni+no and int(c.operation_statistics().num_toffoli_like)==len(ts)
    # object ints may have more than 64 bits; explicit bit-major packing.
    def packed(xs):return np.array([[(v>>i)&1 for v in xs] for i in range(ni+no)],dtype=bool)
    A,B=packed(inputs),packed(expected);qs=km.array([km.q(i) for i in range(ni+no)])
    for seed in [19,131]:
        for i in range(0,len(inputs),64):
            n=min(64,len(inputs)-i);s=km.Simulator(batch_size=n,seed=seed+i,debug_print=False,counting_operations=True)
            s.use_same_registers_as(c);s.write_across_shots(qs,A[:,i:i+n]);s.do(c)
            assert np.array_equal(s.read_across_shots(qs),B[:,i:i+n])
            assert not np.any(s.read_phase_flipped_across_shots())
            s.do(c);assert np.array_equal(s.read_across_shots(qs),A[:,i:i+n])
            assert not np.any(s.read_phase_flipped_across_shots())
    return dict(name=name,Q=c.num_qubits,paid=len(ts),ops=len(c),state_phase_replays=4*len(inputs),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def main():
    rr=[];ns=[];rng=random.Random(2026112897)
    for i,group in enumerate(sources):
        initial=[[(a,b<<24,c) for a,b,c in s] for s in group]
        assert all(polar(t)==polar(initial[0]) for t in initial)
        best=min([search(t,97211+i*100+j,12000) for j,t in enumerate(initial)],key=len)
        assert polar(best)==polar(initial[0])
        # Explicit mixed controls validate the compiler even if no shorter search result exists.
        mixed=[(a,a^b,c) for a,b,c in initial[0]]
        assert polar(mixed)==polar(initial[0])
        rr.append(dict(type=i,steps_requested=36000,best=len(best),candidate_found=len(best)<=97))
        for name,ts in [('mixed99',mixed),('search_best',best)]:
            xx=[0]+[1<<j for j in range(48)]+[(1<<j)|(1<<k) for j in range(48) for k in range(j+1,48)]
            xx += [rng.randrange(1<<48) for _ in range(1024)]
            yy=[reference(group[0],x&((1<<24)-1),x>>24) for x in xx]
            assert all(evaluate(ts,x)==y for x,y in zip(xx,yy))
            zs=[rng.randrange(1<<24) for _ in xx]
            ns.append(native(ts,[x|(z<<48) for x,z in zip(xx,zs)],[x|((z^y)<<48) for x,z,y in zip(xx,zs,yy)],48,24,f'type{i}_{name}'))
    # Eight products implement three independent GF16 observers, NOT a whole field multiplication.
    P=[(10,14,4),(7,15,7),(8,12,6),(9,8,3),(1,4,2),(5,13,6),(3,6,7),(6,11,5)]
    def gf(a,b):
        c=0
        while b:
            if b&1:c^=a
            b>>=1;a<<=1
            if a&16:a^=19
        return c
    def obs(x,y):return sum((((x&gf(k,y)).bit_count()&1)<<i) for i,k in enumerate([1,2,4]))
    ts=[(a,b<<4,c) for a,b,c in P]
    assert all(evaluate(ts,x)==obs(x&15,x>>4) for x in range(256))
    xx=list(range(2048));yy=[x^(obs(x&15,(x>>4)&15)<<8) for x in xx]
    ns.append(native(ts,xx,yy,8,3,'partial_GF16_rank8'))
    receipt=dict(search=rr,native=ns,scope='Local tensor kernels only; no complete DQI splice or score claim.')
    (D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
