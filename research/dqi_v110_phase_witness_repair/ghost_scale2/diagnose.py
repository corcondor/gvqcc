from collections import Counter
from pathlib import Path
import functools, operator, struct, json, sys, random
import numpy as np
import direct_codec as F
from crt_native_frame import P,read_capture,field_words
from frobenius_projector import mod, sq, frob, project, tr_mom

def gcd(a,b):
    while b: a,b=b,mod(a,b)
    return [F.div(x,a[-1]) for x in a] if a else []

def gcdinv(a,b):
    p=b; x,y=[],[1]
    while a:
        d,r=F.divrem(b,a)
        b,a=a,r
        x,y=y,F.add(x,F.pmul(d,y)) if d and y else x
    assert len(b)==1
    return mod([F.div(k,b[0]) for k in x],p)

def pow2(x,p,k):
    for _ in range(k): x=mod(sq(x),p)
    return x

def projector(p):
    delta=F.add(frob(p),[0,1])
    f=gcd(p,pow2(delta,p,6))
    g,r=F.divrem(p,f)
    assert not r
    e=F.add([1],F.pmul(f,gcdinv(f,g))) if len(g)>1 else [1]
    assert not mod(F.add(e,[1]),f)
    assert not mod(e,g)
    assert not mod(F.add(sq(e),e),p)
    return f,g,e

XS=np.arange(4096);LOG=np.asarray(F.LOG);EXP=np.asarray(F.EXP)
def roots(p):
    v=np.zeros(4096,dtype=np.int64)
    for a in p[::-1]: v=np.where(v,EXP[LOG[v]+LOG[XS]],0)^a
    return set(np.flatnonzero(v==0).tolist())

def kinds(p):
    ans=Counter();x=[0,1]
    for d in range(1,len(p)):
        if len(p)==1:break
        x=pow2(x,p,12)
        g=gcd(p,F.add(x,[0,1]))
        j=0
        while len(g)>1:
            j+=1
            assert (len(g)-1)%d==0
            ans[d,j]=(len(g)-1)//d
            p,r=F.divrem(p,g);assert not r
            g=gcd(p,g)
        x=mod(x,p)
    assert p==[1]
    return ','.join(f'{d}^{e}:{n-ans.get((d,e+1),0)}' for (d,e),n in ans.items() if n>ans.get((d,e+1),0))

def syndromes(path):
    data=Path(path).read_bytes()
    off=4
    for _ in range(int.from_bytes(data[:4],'little')):
        n,=struct.unpack_from('<I',data,off);off+=4
        b=struct.unpack_from('<840Q',data,off);off+=(840+49140+1)*8
        for l in range(n):
            yield [sum((b[12*i+j]>>l&1)<<j for j in range(12)) for i in range(70)]
    assert off==len(data)

def outcomes(path):
    with open(path,'rb') as f:
        while row:=f.read(52):
            n,v,p,q,m,a,c=struct.unpack('<I6Q',row)
            for k in range(n):yield tuple(bool(z>>k&1) for z in (v,p,q,m))

def candidate_moments(xset,s):
    xs=sorted(xset)
    if not xs:return [0]*70
    mat=[[x for x in xs]]
    for _ in range(1,len(xs)):
        mat.append([F.mul(x,y) for x,y in zip(xs,mat[-1])])
    a,*_=F.solve(mat,s[:len(xs)],range(len(xs)))
    return F.moments(dict(zip(xs,a)))

def interpolator(d):
    # #283's evaluation/interpolation on a shortened convolution.
    # Varying tails have length d-1, so exactly 2*d-3 distinct points suffice.
    n=2*d-3
    xs=list(range(n))
    prod=F.locator_of(xs)
    cols=[]
    for x in xs:
        q,r=F.divrem(prod,[x,1]);assert not r
        c=F.inv(F.ev(q,x))
        cols.append([F.mul(c,z) for z in q[:d-1]])
    def apply(p,s):
        evs=[F.mul(F.ev(p[-2:0:-1],x),F.ev(s[:d-1],x)) for x in xs]
        y=s[:d]
        for col,v in zip(cols,evs):
            for i,c in enumerate(col):y[i+1]^=F.mul(c,v)
        return y[::-1]
    return apply

CONV=interpolator(35)

def forney(p,s,rts):
    """Polynomial part of P(X) times the syndrome Laurent series."""
    d=len(p)-1
    n=[0]*d
    for i in range(1,d+1):
        for j in range(i):
            n[i-j-1]^=F.mul(p[i],s[j])
    if d==35:assert CONV(p,s)==n
    dp=[p[i] if i%2 else 0 for i in range(1,d+1)]
    den={x:F.mul(x,F.ev(dp,x)) for x in rts}
    if 0 in den.values(): return None
    return {x:F.div(F.ev(n,x),a) for x,a in den.items()}

def main():
    rng=random.Random(296294)
    caps=read_capture('capture_states.bin')+read_capture('independent_states.bin')
    old=json.load(open('../pad_audit.json'))['detail']
    assert len(caps)==len(old)==528
    types=Counter(); audit=Counter()
    for state,meta in zip(caps,old):
        if meta['split']:continue
        p=field_words(P,state); t=kinds(p);types[t]+=1
        f,g,e=projector(p); v=[rng.randrange(4096) for _ in range(35)]
        want=F.moments({x:F.ev(v,x) for x in roots(p) if x})
        got=tr_mom(p,mod(F.pmul(v,e),p))
        audit[t,want==got]+=1
    result={'original_unsupported':dict(types),'all70_arbitrary_v':[[t,b,n] for (t,b),n in audit.items()]}
    print(json.dumps(result),flush=True)
    if len(sys.argv)>1:
        ss=list(syndromes('../joint_work/audit/saved.bin'))
        for path in sys.argv[1:]:
            states=read_capture(path);n=len(states);assert n==len(ss)
            counts=Counter(); sep=Counter(); losses=Counter()
            which='new' if 'new' in path else 'old'
            amplitudes=Counter(); outs=list(outcomes('../native_new_out.bin' if 'native' in path else '../'+which+'_out.bin'));assert len(outs)==n
            for j,(s,state,err) in enumerate(zip(ss,states,outs)):
                canonical,v,*_=F.forward(s)
                truth=roots(canonical)-{0}
                p=field_words(P,state); observed=roots(p)-{0}
                # Distinct coordinate conventions tested, not chosen per case.
                scaled={F.mul(2,x) for x in truth}
                invscaled={F.div(x,2) for x in truth}
                f,g,e=projector(p)
                assert roots(f)-{0}==observed
                ut={F.div(x,2) for x in observed} if which=='new' else observed
                ok=candidate_moments(ut,s)==s
                assert ok==(truth<=ut)
                if ok:
                    # Restore P to the outer frame. Monicity scales coefficient i by 2^(i-d).
                    q=[F.mul(co,F.EXP[((i-(len(p)-1))*F.LOG[2])%4095]) for i,co in enumerate(p)] if which=='new' else p
                    got=forney(q,s,ut)
                    if got is None: amplitudes['multiple_physical_root']+=1
                    else:
                        want={x:F.ev(v,x) for x in truth}
                        assert {x:m for x,m in got.items() if m}==want
                        amplitudes['raw_s_amplitudes_exact']+=1
                sep[(len(truth)==len(ut) and ok,ok,*err)]+=1
                if not ok:losses[len(truth),len(truth-ut)]+=1
                counts[(len(truth),len(truth-observed),len(observed-truth),len(scaled-observed),len(invscaled-observed))]+=1
            result[which+'_paired_outcomes']={'columns':['exact_support','all70_possible','value_error','phase_error','dirty_Q','input_mask_error','count'],
                'forney':dict(amplitudes),'counts':[[*k,v] for k,v in sorted(sep.items())],'missing_by_weight':[[*k,v] for k,v in sorted(losses.items())]}
            print(which,'paired outcomes',sep,'forney',amplitudes,flush=True)
            result[path]=[[*k,v] for k,v in sorted(counts.items())]
            print(path, 'summary', [sum(v for k,v in counts.items() if k[i]==0) for i in range(1,5)], 'of', n,flush=True)
    Path('../projector_audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
