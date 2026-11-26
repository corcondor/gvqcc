"""Exact affine-frame resynthesis of native X/CX/Z_POW windows.

Each emitted window has the same affine exit map and the same multiset of
integer phase coefficients on entrance parities. No numerical approximation,
gate-set substitution, or claim about a globally optimal circuit is made.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, random, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'recovered'/'V79'))
from native_kmb import NativeKMB,Op
from emit_coset_hmr import write_hmr

def bits(x):
    while x:
        b=x&-x;yield b.bit_length()-1;x^=b

def solver(rows,n):
    tab={}
    for i,r in enumerate(rows):
        v=r&((1<<n)-1);c=1<<i
        while v:
            p=v.bit_length()-1
            if p not in tab:tab[p]=(v,c);break
            a,b=tab[p];v^=a;c^=b
        else:raise AssertionError('singular linear frame')
    def solve(mask):
        v=mask&((1<<n)-1);c=0
        while v:
            p=v.bit_length()-1;a,b=tab[p];v^=a;c^=b
        k=(mask>>n)&1
        for j in bits(c):k^=(rows[j]>>n)&1
        return c,k
    return solve

def apply(rows,op,n):
    if op.raw==17:rows[op.wires[0]]^=1<<n
    elif op.raw==33:rows[op.wires[1]]^=rows[op.wires[0]]
    else:raise AssertionError(op)

def affine_finish(rows,target,n,seed=0):
    solve=solver(rows,n)
    coeff=[solve(t) for t in target]
    matrix=[c for c,k in coeff];offset=[k for c,k in coeff]
    orders=[list(range(n)),list(range(n-1,-1,-1)),sorted(range(n),key=lambda i:matrix[i].bit_count())]
    rng=random.Random(seed)
    for _ in range(2):
        order=list(range(n));rng.shuffle(order);orders.append(order)
    best=None
    for order in orders:
        m=matrix.copy();gs=[];done=set()
        for i in order:
            if not (m[i]>>i)&1:
                cand=[j for j in range(n) if j not in done and (m[j]>>i)&1]
                j=min(cand,key=lambda j:(m[j]^m[i]).bit_count())
                m[i]^=m[j];gs.append(Op(33,(j,i)))
            js=[j for j in range(n) if j!=i and (m[j]>>i)&1]
            for j in js:m[j]^=m[i];gs.append(Op(33,(i,j)))
            done.add(i)
        assert m==[1<<i for i in range(n)]
        seq=list(reversed(gs))+[Op(17,(i,)) for i,k in enumerate(offset) if k]
        if best is None or len(seq)<len(best):best=seq
    rr=rows.copy()
    for op in best:apply(rr,op,n)
    assert rr==target
    return best

def analyze(ops,n,rotation_ids):
    rows=[1<<i for i in range(n)];rot=[];r=iter(rotation_ids)
    for op in ops:
        if op.raw==19:rot.append((rows[op.wires[0]],next(r)))
        else:apply(rows,op,n)
    return rows,rot

def greedy_segment(ops,n,rotation_ids,mode,seed):
    target,rot=analyze(ops,n,rotation_ids)
    rows=[1<<i for i in range(n)];out=[];newids=[]
    pending=list(rot)
    rng=random.Random(seed)
    while pending:
        solve=solver(rows,n)
        candidates=[]
        for pos,(mask,rid) in enumerate(pending):
            c,k=solve(mask)
            assert c,'constant phase encountered'
            js=list(bits(c))
            candidates.append((len(js)-1+k,pos,c,k,mask,rid))
            if mode==0:break
        minimum=min(v[0] for v in candidates)
        options=[v for v in candidates if v[0]==minimum]
        if mode==2:rng.shuffle(options)
        picked=min(options,key=lambda v:(v[4].bit_count(),v[1])) if mode==1 else options[0]
        _,pos,c,k,mask,rid=picked;js=list(bits(c))
        if len(js)>1:
            choices=[]
            for pivot in js:
                rr=rows.copy();rr[pivot]=mask
                ss=solver(rr,n)
                future=[]
                for m,r in pending:
                    if r!=rid:
                        a,b=ss(m);future.append(max(0,a.bit_count()-1)+b)
                # Favor preserving a requested exit row and cheaply reaching
                # the nearest next phase. This is only a search heuristic.
                nearest=min(future,default=0)
                final_hit=int(mask in target)-int(rows[pivot] in target)
                choices.append((nearest-final_hit*.25, rows[pivot].bit_count(),pivot))
            pivot=min(choices)[2]
        else:pivot=js[0]
        for j in js:
            if j!=pivot:
                op=Op(33,(j,pivot));out.append(op);apply(rows,op,n)
        if k:
            op=Op(17,(pivot,));out.append(op);apply(rows,op,n)
        assert rows[pivot]==mask
        out.append(Op(19,(pivot,)));newids.append(rid)
        pending.pop(pos)
    out+=affine_finish(rows,target,n,seed)
    final,newrot=analyze(out,n,newids)
    assert final==target and sorted(newrot)==sorted(rot)
    return out,newids

def optimize(stem,outstem,rounds=3):
    start=time.time();stem=Path(stem);outstem=Path(outstem);outstem.parent.mkdir(parents=True,exist_ok=True)
    k=NativeKMB.read(str(stem)+'.kmb');meta=json.loads(Path(str(stem)+'.json').read_text());n=k.header[1]
    output=[];ids=[];ri=0;i=0;reports=[]
    while i<len(k.ops):
        if k.ops[i].raw not in (17,33,19):output.append(k.ops[i]);i+=1;continue
        j=i
        while j<len(k.ops) and k.ops[j].raw in (17,33,19):j+=1
        window=k.ops[i:j];nr=sum(op.raw==19 for op in window);oldids=list(range(ri,ri+nr));ri+=nr
        best=window;bestids=oldids
        if len(window)>2 and len(window)-nr>2:
            for mode in range(rounds):
                seq,seqids=greedy_segment(window,n,oldids,mode%3,(i+7)*31+mode)
                if len(seq)<len(best):best,bestids=seq,seqids
        if len(best)<len(window):reports.append({'start':i,'end':j,'before':len(window),'after':len(best),'rotations':nr})
        output.extend(best);ids.extend(bestids);i=j
    assert ri==len(meta['angles'])
    angles=[int(meta['angles'][j]) for j in ids];tags=[meta['tags'][j] for j in ids]
    write_hmr(k,Path(str(outstem)+'.kmb'),output,angles,n,True)
    stats=collections.Counter(o.raw for o in output)
    r={'source':str(stem),'source_sha256':hashlib.sha256(Path(str(stem)+'.kmb').read_bytes()).hexdigest(),'source_ops':len(k.ops),'ops':len(output),'saved_ops':len(k.ops)-len(output),'ccx':stats[49],'cx':stats[33],'rotations':stats[19],'generic':sum(a%(1<<125)!=0 for a in angles),'width':n,'improved_windows':len(reports),'seconds':time.time()-start,'exact_affine_and_phase_window_certificates':'PASS','windows':reports}
    Path(str(outstem)+'.json').write_text(json.dumps({'stats':r,'angles':[str(a) for a in angles],'tags':tags},separators=(',',':')))
    Path(str(outstem)+'.optimizer.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({a:b for a,b in r.items() if a!='windows'}),flush=True)
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stem');p.add_argument('outstem');p.add_argument('--rounds',type=int,default=3);a=p.parse_args();optimize(a.stem,a.outstem,a.rounds)
