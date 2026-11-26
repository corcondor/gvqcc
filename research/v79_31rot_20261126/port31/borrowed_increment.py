"""Borrowed-register increment using Gidney's 2015 construction.

Independent Python 3 native-KMB implementation of the reversible construction
in https://algassert.com/circuits/2015/06/12/Constructing-Large-Increment-Gates.html
and the author's linked executable example. Every borrowed wire is restored.
"""
from functools import lru_cache
from coherent_horner import Op, mcx


def xgate(q):return Op(17,(q,))
def cx(a,b):return Op(33,(a,b))
def ccx(a,b,c):return Op(49,(a,b,c))


def fanout(controls, targets, width):
    if not targets:return []
    if len(targets)==1:return mcx(controls,targets[0],width)
    if len(controls)<=2:
        return sum((mcx(controls,t,width) for t in targets),[])
    chain=[cx(a,b) for a,b in zip(targets,targets[1:])]
    return list(reversed(chain))+mcx(controls,targets[0],width)+chain


@lru_cache(None)
def increment(bits,width=36):
    """Little-endian bits <- bits+1 mod2^n; other wires arbitrary/restored."""
    bits=tuple(bits);n=len(bits)
    if n<=2:
        return tuple(o for i in reversed(range(n)) for o in mcx(bits[:i],bits[i],width))
    spare=[q for q in range(width) if q not in bits]
    if not spare:raise ValueError('one borrowed wire is required')
    if len(spare)>=n:
        # Two reversible subtraction sweeps cancel the borrowed register.
        b=spare[:n];up=[];down=[]
        for i in range(n-1):
            up.extend([cx(b[i],bits[i]),ccx(bits[i],b[i+1],b[i]),ccx(bits[i],b[i],b[i+1])])
            down.extend([cx(b[i+1],bits[i]),ccx(bits[i],b[i+1],b[i]),ccx(bits[i],b[i],b[i+1])])
        sweep=up+[cx(b[-1],bits[-1])]+list(reversed(down))
        carry=[cx(b[0],q) for q in bits[:-1]]
        garbage=[xgate(q) for q in b[1:]]
        return tuple([xgate(bits[-1])]+carry+garbage+sweep+garbage+sweep+carry)
    cut=(n+1)//2;low=list(bits[:cut]);high=list(bits[cut:]);borrow=spare[0]
    high_inc=list(increment(tuple([borrow]+high),width))
    low_inc=list(increment(tuple(low),width))
    toggle=fanout(low,high+[borrow],width)
    complement=[xgate(q) for q in high]
    return tuple(complement+toggle+high_inc+[xgate(borrow)]+toggle+complement+high_inc+[xgate(borrow)]+low_inc)


def controlled_increment(control,bits,width=36,negative=False):
    ops=list(increment(tuple([control]+list(bits)),width))+[xgate(control)]
    return list(reversed(ops)) if negative else ops


def validate():
    import numpy as np,json,hashlib
    rows=[]
    rng=np.random.default_rng(312026)
    for n in range(1,11):
        for Q in sorted({n+2,2*(n+1)}):
            # n data + one flag; one-borrow and many-borrow constructions.
            inputs=np.arange(1<<Q,dtype=np.uint64)
            one=(1<<len(inputs))-1
            pack=lambda a:int.from_bytes(np.packbits(a,bitorder='little').tobytes(),'little')
            s=[pack((inputs>>q)&1) for q in range(Q)];initial=s[:]
            ops=controlled_increment(0,list(range(1,n+1)),Q)
            for o in ops:
                v=one
                for q in o.wires[:-1]:v&=s[q]
                s[o.wires[-1]]^=v
            words=((inputs>>1)&((1<<n)-1));words=(words+(inputs&1))&((1<<n)-1)
            assert s[0]==initial[0]
            assert s[1:n+1]==[pack((words>>j)&1)for j in range(n)]
            assert s[n+1:]==initial[n+1:]
            rows.append({'data_bits':n,'physical_width':Q,'assignments':len(inputs),'CCX':sum(o.raw==49 for o in ops),'instructions':len(ops)})
    for n in [11,15,18,21]:
        Q=36;inputs=rng.integers(0,1<<Q,4096,dtype=np.uint64)
        one=(1<<len(inputs))-1;pack=lambda a:int.from_bytes(np.packbits(a,bitorder='little').tobytes(),'little')
        s=[pack((inputs>>q)&1)for q in range(Q)];initial=s[:]
        ops=controlled_increment(0,list(range(1,n+1)),Q)
        for o in ops:
            v=one
            for q in o.wires[:-1]:v&=s[q]
            s[o.wires[-1]]^=v
        words=(((inputs>>1)&((1<<n)-1))+(inputs&1))&((1<<n)-1)
        assert s[0]==initial[0] and s[n+1:]==initial[n+1:]
        assert s[1:n+1]==[pack((words>>j)&1)for j in range(n)]
        rows.append({'data_bits':n,'physical_width':Q,'assignments':4096,'scope':'random arbitrary borrowed bits','CCX':sum(o.raw==49 for o in ops),'instructions':len(ops)})
    return {'controlled_increment_and_all_borrowed_wire_restoration':'PASS','rows':rows}


if __name__=='__main__':
    import json
    from pathlib import Path
    d=validate();Path(__file__).with_name('borrowed_increment_validation.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
