"""Independent KMB replay: 4095 affine leaves, all symbolic HMR corrections,
64 packed sparse-error fixtures. Uses polynomial multiply, not emitter tables."""
import array, struct, random, hashlib, json, sys
from pathlib import Path
F=4096;M=4095;N=35;FLAG=49140;HM=49141

def mul(a,b):
    z=0
    while b:
        if b&1:z^=a
        b>>=1;a<<=1
        if a&F:a^=0x1053
    return z

def ev(p,x):
    z=0
    for a in reversed(p):z=mul(z,x)^a
    return z

def inv(a):
    assert a;r=1;n=4094
    while n:
        if n&1:r=mul(r,a)
        a=mul(a,a);n>>=1
    return r

def prod(a,b):
    z=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):z[i+j]^=mul(x,y)
    return z

def fixtures():
    R=random.Random(81213);ex=[1]
    for _ in range(1,M):ex.append(mul(ex[-1],2))
    assert len(set(ex))==M and mul(ex[-1],2)==1
    q=[0]*851;c=[0]*(HM+1);phase=0
    for l in range(64):
        w=l if l<=35 else R.randrange(27,36);js=R.sample(range(M),w);es=[R.randrange(1,F) for _ in js];rs=[ex[j] for j in js];P=[1]
        for r in rs:P=prod(P,[r,1])
        V=[0]*N
        for r,e in zip(rs,es):
            h=[0]*(len(P)-1);h[-1]=P[-1]
            for i in range(len(h)-2,-1,-1):h[i]=P[i+1]^mul(r,h[i+1])
            assert P[0]==mul(r,h[0]);s=mul(e,inv(ev(h,r)))
            for i,v in enumerate(h):V[i]^=mul(s,v)
        P=[0]*(N-w)+P;assert len(P)==N+1 and P[N]==1
        assert all(ev(P,r)==0 and ev(V,r)==e for r,e in zip(rs,es))
        for i,v in enumerate(P[:N]+V):
            for b in range(12):q[12*i+b]|=((v>>b)&1)<<l
        masks=[R.randrange(F) for _ in range(M)]
        if l==36:masks=[0]*M
        if l==37:masks=[1<<(j%12) for j in range(M)]
        for j,v in enumerate(masks):
            for b in range(12):c[12*j+b]|=((v>>b)&1)<<l
        phase|=(sum((e&masks[j]).bit_count() for j,e in zip(js,es))&1)<<l
    return ex,q,c,phase

def read(path):
    d=memoryview(Path(path).read_bytes());head=struct.unpack_from('<16s4I9Q',d);assert head[0].hex()=='d750c7d5c329d326e3cc9f6834f2b8bf' and head[1:5]==(2,851,HM+1,2*N+M)
    i=104;cols={};regs=set()
    while i<len(d):
        k,n=struct.unpack_from('<QQ',d,i);i+=16;v=d[i:i+n];i+=n
        if k==0:
            l,r=struct.unpack_from('<II',v);assert r==12;name=bytes(v[8:8+l]).decode();j=int(name[1:]);assert name[0] in 'PVE' and name not in regs and 0<=j<(M if name[0]=='E' else N);regs.add(name)
            off=12*j+(420 if name[0]=='V' else 0);assert struct.unpack_from('<12I',v,8+l)==tuple((off+b)|(0 if name[0]=='E' else 1<<31) for b in range(12))
        elif k==1:cols[k]=v
        else:cols[k]=v.cast('I')
    assert len(regs)==2*N+M and len(cols[1])==head[5] and [len(cols[k]) for k in [2,5,7,8,9]]==list(head[6:11]);pos=[0]*10
    for t in cols[1]:
        a=b=c=-1;m=k=0;ar=(t>>4)&3
        if ar==1:a=cols[7][pos[7]];pos[7]+=1
        if ar==2:a=cols[5][pos[5]];b=cols[6][pos[6]];pos[5]+=1;pos[6]+=1
        if ar==3:a=cols[2][pos[2]];b=cols[3][pos[3]];c=cols[4][pos[4]];pos[2]+=1;pos[3]+=1;pos[4]+=1
        if t&64:m=cols[8][pos[8]];pos[8]+=1
        if t&128:k=cols[9][pos[9]];pos[9]+=1
        yield t,a,b,c,m,k
    assert all(pos[k]==len(cols[k]) for k in range(2,10))

def verify(path):
    ex,q,c,target=fixtures();init=q[:];ci=c[:];s=[1<<i for i in range(840)];R=random.Random(715);active=(1<<64)-1;phase=paid=0;stack=[];seen=set();gates=iter(read(path));ops=0
    def sim(g):
        nonlocal active,phase,paid,ops
        ops+=1;t,a,b,d,m,k=g;u=active&(c[k] if t&128 else active)
        if t==129:stack.append(active);active=u;return
        if t==1:active=stack.pop();return
        t&=127
        if t==17:q[a]^=u
        elif t==33:q[b]^=u&q[a]
        elif t==34:z=u&(q[a]^q[b]);q[a]^=z;q[b]^=z
        elif t==49:q[d]^=u&q[a]&q[b];paid+=u.bit_count()
        elif t==32:phase^=u&q[a]&q[b]
        elif t==64:c[m]&=~u
        elif t==65:c[m]|=u
        elif t==80:
            r=R.getrandbits(64);phase^=u&r&q[a];q[a]&=~u;c[m]=(c[m]&~u)|(u&r)
        else:raise AssertionError(g)
    def expect(t,a=-1,b=-1,d=-1,m=0,k=0):
        g=next(gates);assert g==(t,a,b,d,m,k),(g,(t,a,b,d,m,k));sim(g)
    for g in gates:
        t,a,b,d,m,k=g;sim(g)
        if t==33:assert a<840 and b<840;s[b]^=s[a]
        elif t==34:assert a<840 and b<840;s[a],s[b]=s[b],s[a]
        elif t==17:assert a<840;s[a]^=1<<840
        else:
            assert g==(64,-1,-1,-1,FLAG,0);h=next(gates);sim(h);assert h[0:5]==(193,-1,-1,-1,FLAG) and h[5]%12==0;j=h[5]//12;assert j not in seen and 0<=j<M;seen.add(j)
            for b in range(1,12):expect(193,m=FLAG,k=12*j+b)
            expect(129,k=FLAG)
            p=[0]*12;v=[0]*12;y=1;x=ex[j]
            for a in range(N):
                for b in range(12):
                    z=mul(y,1<<b)
                    for d in range(12):
                        if z>>d&1:p[d]|=1<<(12*a+b);v[d]|=1<<(420+12*a+b)
                y=mul(y,x)
            for b in range(12):
                if (y^4095)>>b&1:p[b]|=1<<840
            assert p==s[:12] and v==s[420:432]
            # Exact structural HMR proof: each measured product has both
            # original factors still live, CZ conditioned on its own result.
            expect(49,0,1,840)
            for b in range(2,12):expect(49,838+b,b,839+b)
            for b in range(12):expect(160,850,420+b,k=12*j+b)
            for b in range(11,1,-1):expect(80,839+b,m=HM);expect(160,838+b,b,k=HM)
            expect(80,840,m=HM);expect(160,0,1,k=HM);expect(1);expect(64,m=FLAG)
    assert len(seen)==M and s==[1<<i for i in range(840)] and q==init and c[:FLAG]==ci[:FLAG] and c[FLAG]==0 and not stack and phase==target
    result=dict(sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),ops=ops,exact_affine_points=M,all_hmr_outcomes=True,restoration=True,independent_packed_cases=64,value_errors=0,phase_errors=0,mean_paid=paid/64)
    print(json.dumps(result),flush=True);Path(path+'.verified.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':verify(sys.argv[1])
