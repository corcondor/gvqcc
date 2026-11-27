"""Controlled fixed scale. Real s,t stay intact; F selects virtual s,t or 1.
One dirty transport wire and one additional dirty control helper, both restored.
No input-dependent host branches. Pooled classical measurement masks.
"""
import collections
import kickmix as km
from fixed_transport import make
TAPE=make()
COUNTS=collections.Counter()
def emit_controlled(b,x,s,t,F,dirty,helper):
    x,s,t=map(list,(x,s,t));data=x+s+t+[F,dirty,helper]
    assert len(x)==len(s)==len(t)==12 and len(set(map(str,data)))==39
    entry=b.num_allocated_qubits;out=list(b.alloc_qubits(11));m=list(b.alloc_bits(11));parity=b.alloc_bits(1)[0]
    b.bit_store(parity,False)
    w=x+s+t+out+[dirty];ref=[0]*48;ref[12]=ref[24]=1
    scalar=lambda i:12<=i<36
    def split(a,c):
        assert scalar(a)!=scalar(c)
        return (a,c) if scalar(a) else (c,a)
    with b.mark('uniform_controlled_scale'):
        for op,*v in TAPE:
            if op=='CCX':
                a,r=split(v[0],v[1]);dst=v[2];assert not scalar(dst)
                if ref[a]:b.cx(w[r],w[dst]);b.x(w[a])
                b.ccx(helper,w[r],w[dst]);b.ccx(F,w[a],helper)
                b.ccx(helper,w[r],w[dst]);b.ccx(F,w[a],helper)
                if ref[a]:b.x(w[a])
            elif op in ('CZ_MASK','CZ_IF'):
                a,r=split(v[0],v[1]);mask=(1<<v[2]) if op=='CZ_IF' else v[2]
                ids=[j for j in range(11) if mask>>j&1];assert ids
                for j in ids:b.cx(m[j],parity)
                if ref[a]:b.cz(w[r],parity);b.x(w[a])
                b.ccz(helper,w[r],parity);b.ccx(F,w[a],helper)
                b.ccz(helper,w[r],parity);b.ccx(F,w[a],helper)
                if ref[a]:b.x(w[a])
                for j in ids:b.cx(m[j],parity)
            elif op=='HMR':b.hmr(w[v[0]],m[v[1]])
            elif op=='CX':
                a,r=v;assert scalar(a)==scalar(r)
                if scalar(a):ref[r]^=ref[a]
                b.cx(w[a],w[r])
            elif op=='SWAP':
                a,r=v;assert scalar(a)==scalar(r)
                if scalar(a):ref[a],ref[r]=ref[r],ref[a]
                b.swap(w[a],w[r])
            elif op=='X':
                if scalar(v[0]):ref[v[0]]^=1
                b.x(w[v[0]])
            else:raise ValueError(op)
    assert ref[12:36]==[1]+[0]*11+[1]+[0]*11
    b.free(parity);b.free(m);b.free(out);assert b.num_allocated_qubits==entry
    COUNTS['controlled']+=1

def cscale_at_width(b,ar,F,tops,x,y):
    import dqi_int_convtest as CT
    live=set(CT.TR['live']);excluded={int(str(q)[1:]) for q in [F]+list(x)+list(y)+[q for t in tops for q in t]}
    assert len(live)==b.num_allocated_qubits and excluded<=live and len(live-excluded)>=2
    d,h=map(km.q,sorted(live-excluded)[:2])
    print('UNIFORM CSCALE',b.num_allocated_qubits,'tops',len(tops),'dirty',d,h,flush=True)
    for t in tops:emit_controlled(b,t,x,y,F,d,h)
