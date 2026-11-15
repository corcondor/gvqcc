"""Check simultaneous marker masks across the longest incumbent peaks."""
import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

from gauge_probe import MAX_X, SOURCE_SHA, gate, physical_trace
from gauge_sat import solve_interval
from peak_probe import annotate, dependencies, groups, snapshots

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--limit',type=int,default=12)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    counts,depth,ref=annotate(ops)
    w,mask=physical_trace(ops)
    cases=[]
    for a,b in sorted(groups(counts,46),key=lambda r:r[0]-r[1])[:args.limit]:
        start=a-1
        while depth[start] or counts[start]>=46:
            start-=1
        stop=b+1
        while depth[stop] or counts[stop]>=46:
            stop+=1
        cases.append((a,b,start,stop))
    states,one=snapshots(ops,np.arange(1,MAX_X+1,dtype=np.uint32),{z for a,b,s,z in cases})
    result=[]
    for a,b,start,stop in cases:
        d=dependencies(states[stop],one)
        row=dict(a=a,b=b,start=start,stop=stop,affine_dependencies=len(d))
        if not d:
            row.update(result='NO_AFFINE_KERNEL')
        elif any(start<=i<stop for i in ref) or w[start][25]!=mask or w[stop][25]!=mask:
            row.update(result='OUTSIDE_BRANCH_SCOPE')
        else:
            row.update(solve_interval(ops,w,mask,start,stop,d,True,4000))
        result.append(row)
        print(row,flush=True)
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,cases=result),indent=2)+'\n')

if __name__=='__main__':
    main()
