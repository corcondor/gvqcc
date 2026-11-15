"""Exact injectivity audit of marker encoding at constrained decoder cuts."""
import argparse
from itertools import combinations
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

from gauge_probe import MAX_X, SOURCE_SHA, gate, physical_trace, propagate
from peak_probe import snapshots

def pack(w):
    state=np.zeros(MAX_X,dtype=np.uint64)
    for j,s in enumerate(w):
        if j!=25:
            bits=np.unpackbits(np.frombuffer(s.to_bytes((MAX_X+7)//8,'little'),dtype=np.uint8),bitorder='little')[:MAX_X]
            state|=(bits.astype(np.uint64) << np.uint64(j))
    return state

def collisions(w,d):
    state=pack(w)
    order=np.argsort(state[63:],kind='stable')
    small=state[:63]^np.uint64(d)
    large=state[63:][order]
    ports=np.searchsorted(large,small)
    eq=(ports<len(large)) & (large[np.minimum(ports,len(large)-1)]==small)
    return [(int(j)+1, int(order[ports[j]])+64) for j in np.flatnonzero(eq)]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    d,m=physical_trace(ops)
    cases=((632,7630),(632,7644),(8400,23638))
    states,mask=snapshots(ops,np.arange(1,MAX_X+1,dtype=np.uint32),{t for _,t in cases})
    rs=[]
    for start,stop in cases:
        for bits in [q for k in (1,2,3) for q in combinations((22,23,24),k)]:
            initial=sum(1<<q for q in bits)
            end,last,kind,stats=propagate(ops,d,m,initial,start,stop)
            if end!=stop:
                continue
            failure=collisions(states[stop],last)
            row=dict(start=start,stop=stop,initial=list(bits),end_mask=last,collisions=failure)
            print(start,stop,bits,len(failure),failure[:3],flush=True)
            rs.append(row)
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,checked=MAX_X,encodings=rs),indent=2)+'\n')

if __name__=='__main__':
    main()
