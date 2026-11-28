"""D16 shear conjugation. Keep the original nonlinear products, compress fanout."""
from collections import Counter
from functools import reduce
from itertools import combinations
from operator import xor
from pathlib import Path
import json
import random
import arithmetic as ar

def setbits(x):
    while x:
        b=x&-x
        yield b.bit_length()-1
        x^=b

def output_frame(masks, n):
    rows=[sum((m>>i&1)<<j for j,m in enumerate(masks)) for i in range(n)]
    def plan(order):
        pivots={}
        selected=[]
        for i in order:
            v, c=rows[i],0
            while v and v.bit_length() in pivots:
                k,a=pivots[v.bit_length()]
                v,c=v^k,c^a
            if v:
                pivots[v.bit_length()]=(v,c^(1<<len(selected)))
                selected.append(i)
        chosen=set(selected)
        frame=[]
        for i,y in enumerate(rows):
            if i in chosen: continue
            c=0
            while y:
                k,a=pivots[y.bit_length()]
                y,c=y^k,c^a
            assert rows[i]==reduce(xor,(rows[selected[j]] for j in setbits(c)),0)
            frame.extend((selected[j],i) for j in setbits(c))
        retained=sum(1<<i for i in selected)
        assert all(m & retained for m in masks)
        return len(frame)+sum((m & retained).bit_count()-1 for m in masks),retained,frame
    rng=random.Random(20261128)
    orders=[list(range(n)),sorted(range(n),key=lambda i:rows[i].bit_count())]
    orders.extend(rng.sample(range(n),n) for _ in range(48))
    return min(map(plan,orders))

def emit_pair(path):
    w=json.loads(path.read_text())
    inputs,outputs=w["input_wires"],w["output_wires"]
    pairs=list(ar.masks(path.parent/w["input_forms"]))
    masks=[m for m, in ar.masks(path.parent/w["output_forms"])]
    assert len(set(inputs+outputs))==len(inputs)+len(outputs)
    _,retained,frame=output_frame(masks,len(outputs))
    from io import BytesIO
    baseline,candidate=BytesIO(),BytesIO()
    ar.emit_product(baseline,path)
    setup=[f"CX q{outputs[a]} q{outputs[b]}\n".encode() for a,b in frame]
    candidate.writelines(setup)
    for (a,b),m in zip(pairs,masks,strict=True):
        ar.product_term(candidate,ar.support(a,inputs),ar.support(b,inputs),ar.support(m&retained,outputs))
    candidate.writelines(reversed(setup))
    return w,baseline.getvalue(),candidate.getvalue()

def test(w, old, new, pairs, masks, seed):
    import numpy as np
    import kickmix as km
    from tempfile import TemporaryDirectory
    inputs,outputs=w["input_wires"],w["output_wires"]
    n=len(inputs)
    # 667 monomial probes; arbitrary nonzero outputs and random inputs included.
    deterministic=[0]+[1<<i for i in range(n)]+[(1<<i)|(1<<j) for i,j in combinations(range(n),2)]
    rng=np.random.default_rng(seed)
    vals=np.array(deterministic+list(rng.integers(1<<n,size=1024)),dtype=np.uint64)
    x=((vals[None,:]>>np.arange(n,dtype=np.uint64)[:,None])&1).astype(bool)
    y=rng.integers(2,size=(len(outputs),len(vals)),dtype=np.uint8).astype(bool)
    expected=y.copy()
    for (a,b),m in zip(pairs,masks,strict=True):
        d=np.logical_xor.reduce(x[list(setbits(a))],axis=0)&np.logical_xor.reduce(x[list(setbits(b))],axis=0)
        expected[list(setbits(m))]^=d
    with TemporaryDirectory(prefix="product-",dir=".") as tmp:
        f=Path(tmp)/"t.kmx"
        for assembly in (old,new):
            f.write_bytes(assembly)
            c=km.Circuit.from_file(f,format="kmx")
            sim=km.Simulator(len(vals),seed=seed)
            sim.use_same_registers_as(c)
            for i,row in zip(inputs,x):sim.write_across_shots(km.q(i),row)
            for i,row in zip(outputs,y):sim.write_across_shots(km.q(i),row)
            sim.do(c)
            for i,row in zip(inputs+outputs,np.concatenate((x,expected))):
                assert np.array_equal(sim.read_across_shots(km.q(i)),row),i
            assert not sim.read_phase_flipped_across_shots().any()
    return len(vals)

if __name__=="__main__":
    import sys
    d=Path(sys.argv[1]); dest=Path(sys.argv[2]); dest.mkdir(exist_ok=True)
    ledger={}
    for p in sorted(d.glob("field_*_wiring_*.json")):
        w,old,new=emit_pair(p)
        pairs=list(ar.masks(p.parent / w["input_forms"]))
        masks=[m for m, in ar.masks(p.parent / w["output_forms"])]
        assert old.count(b"CCX ")==new.count(b"CCX ")==len(pairs)
        result=dict(paid=len(pairs),old_ops=old.count(b"\n"),new_ops=new.count(b"\n"),
                    lanes=test(w,old,new,pairs,masks,100+len(ledger)))
        ledger[p.stem]=result
        for arm,data in [("old",old),("new",new)]: (dest/f"{p.stem}.{arm}.kmx").write_bytes(data)
        print(p.stem,result,flush=True)
    (dest/"components.json").write_text(json.dumps(ledger,indent=2)+"\n")
