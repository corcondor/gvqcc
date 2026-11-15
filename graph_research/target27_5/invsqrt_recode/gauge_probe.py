"""Screen a 63-point branch marker propagated as an affine frame."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'highest_inv_next'))
from quadratic_phase import MAX_X, SOURCE_SHA, advance, columns, gate

DATA={'X','CX','CCX','CSWAP','SWAP','HMR','R'}
SPANS=((631,7644),(8399,23642))

def physical_trace(ops):
    xt=np.arange(1,64,dtype=np.uint32)
    w=columns(xt)
    m=(1<<len(xt))-1
    before=[]
    for op,qs in ops:
        before.append(w[:])
        advance(op,qs,w,m)
    return before,m

def one_gate(original,delta,op,qs,m):
    if op=='CX':
        a,b=qs
        return delta^((delta>>a&1)<<b)
    if op=='SWAP':
        a,b=qs
        if (delta>>a^delta>>b)&1:
            delta^=(1<<a)|(1<<b)
        return delta
    if op=='CCX':
        a,b,t=qs
        aa,bb=delta>>a&1,delta>>b&1
        effect=(original[a] if bb else 0)^(original[b] if aa else 0)^(m if aa&bb else 0)
        if effect not in (0,m):
            return None
        return delta^((effect==m)<<t)
    if op=='CSWAP':
        a,b,t=qs
        aa=delta>>a&1
        xx=(delta>>b^delta>>t)&1
        effect=((original[b]^original[t]) if aa else 0)^(original[a] if xx else 0)^(m if aa&xx else 0)
        if effect not in (0,m):
            return None
        return delta^(((1<<b)|(1<<t)) if effect==m else 0)
    if op in ('HMR','R'):
        return delta&~(1<<qs[0])
    return delta

def propagate(ops,states,mask,delta,a,b):
    stack=[]
    costs=Counter()
    for i in range(a,b):
        op,qs=ops[i]
        if op=='PUSH_CONDITION':
            stack.append(delta)
        elif op=='POP_CONDITION':
            initial=stack.pop()
            if delta!=initial:
                return i,delta,'guard_data',dict(costs)
        elif op=='R' and delta>>qs[0]&1:
            return i,delta,'asserted_zero',dict(costs)
        new=one_gate(states[i],delta,op,qs,mask)
        if new is None:
            return i,delta,op,dict(costs)
        if new!=delta and op=='HMR':
            costs['hmr_offsets']+=1
        if op in {'Z','CZ','CCZ','Z_POW'} and any(delta>>q&1 for q in qs):
            p=q=mask
            for bit in qs:
                p&=states[i][bit]
                q&=states[i][bit]^(mask if delta>>bit&1 else 0)
            if op=='Z_POW' and p!=q:
                return i,delta,op,dict(costs)
            if p!=q:
                costs['sign_offsets']+=1
                if p^q!=mask:
                    costs['nonconstant_sign_offsets']+=1
        delta=new
        if not delta:
            return i,0,'erased',dict(costs)
    assert not stack
    return b,delta,'success',dict(costs)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--stride',type=int,default=100)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    states,mask=physical_trace(ops)
    stack=0
    depth=[]
    for op,_ in ops:
        depth.append(stack)
        stack+=int(op=='PUSH_CONDITION')-int(op=='POP_CONDITION')
    report=[]
    for a,b in SPANS:
        all_starts=[]
        for s in range(a,b,args.stride):
            cut=next((i for i in range(s,b) if depth[i]==0),None)
            if cut is not None and cut not in all_starts:
                all_starts.append(cut)
        paths=[]
        print('span',a,b,flush=True)
        for s in all_starts:
            runs=[(propagate(ops,states,mask,1<<q,s,b),q) for q in range(46) if q!=25]
            for (end,delta,status,stats),q in runs:
                paths.append(dict(start=s,wire=q,end=end,delta=delta,status=status,
                                  score=(end-s),**stats))
        paths.sort(key=lambda r:(-r['score'],r.get('nonconstant_sign_offsets',0)))
        for r in paths[:5]:print(r,flush=True)
        print('full paths',sum(p['status']=='success' and p['start']==a for p in paths),flush=True)
        report.append(dict(start=a,stop=b,paths=len(paths),best=paths[:70],
                           failures=Counter(p['status'] for p in paths)))
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,branch_size=mask.bit_count(),
                                        gauge_paths=report),indent=2)+'\n')

if __name__=='__main__':
    main()
