"""Try a branch-marker overlay across consecutive peak-width regions."""
import argparse
from bisect import bisect_left,bisect_right
from collections import Counter
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

from gauge_probe import DATA, MAX_X, SOURCE_SHA, SPANS, advance, columns, gate, physical_trace, propagate

def annotate(ops):
    xs=np.arange(1,MAX_X+1,dtype=np.uint32)
    full=columns(xs)
    m=(1<<len(xs))-1
    counts=[]
    frames=[]
    d=[]
    ref25=[]
    for i,(op,qs) in enumerate(ops):
        d.append(len(frames))
        counts.append(sum(v!=0 for v in full))
        if op=='PUSH_CONDITION':
            frames.append(full[:])
        elif op=='POP_CONDITION':
            assert frames.pop()==full
        else:
            advance(op,qs,full,m)
        if 25 in qs:
            ref25.append(i)
    return counts,d,ref25

def groups(counts,w):
    out=[]
    for cut,n in enumerate(counts):
        if n<w:
            continue
        if out and out[-1][1]+1==cut:
            out[-1]=(out[-1][0],cut)
        else:
            out.append((cut,cut))
    return out

def snapshots(ops,xs,selected):
    values=columns(xs)
    mask=(1<<len(xs))-1
    out={}
    for i,(op,qs) in enumerate(ops):
        if i in selected:
            out[i]=values[:]
        advance(op,qs,values,mask)
    return out,mask

def dependencies(values,mask):
    basis={mask.bit_length()-1:(mask,1)}
    dependencies=[]
    for j,value in enumerate(values):
        if j==25:
            continue
        f=1<<(j+1)
        while value:
            p=value.bit_length()-1
            if p not in basis:
                basis[p]=(value,f)
                break
            a,b=basis[p];value^=a;f^=b
        else:
            dependencies.append(f)
    return dependencies

def find(ops,counts,depth,owners,peaks,states,mask,extend,top=8):
    starts,ends={},{}
    ref=sorted(owners)
    for k,(a,b) in enumerate(peaks):
        before=bisect_left(ref,a)
        after=bisect_right(ref,b)
        if before!=after or depth[a] or depth[b+1]:
            # The initial study leaves cross-block peaks for a later solver.
            continue
        left=max(0 if not before else ref[before-1]+1,a-extend)
        right=min(len(ops)-1 if after==len(ref) else ref[after],b+1+extend)
        starts[k]=[j for j in range(a,left-1,-1) if not depth[j] and counts[j]<46]
        ends[k]=[j for j in range(b+1,right+1) if not depth[j] and counts[j]<46]
    cut_set={i for v in list(starts.values())+list(ends.values()) for i in v}
    xs=np.unique(np.r_[np.arange(1,1300),np.random.default_rng(33205).integers(1,MAX_X+1,3200),MAX_X]).astype(np.uint32)
    sample_data,ms=snapshots(ops,xs,cut_set)
    null={k:dependencies(z,ms) for k,z in sample_data.items()}
    paths=[]
    for k,(a,b) in enumerate(peaks):
        row=dict(a=a,b=b,length=b-a+1,solutions=[])
        for start in starts.get(k,[])[:top]:
            for q in range(46):
                if q==25 or not states[start][25]==mask:
                    continue
                for stop in ends.get(k,[])[:top]:
                    end,delta,kind,stats=propagate(ops,states,mask,1<<q,start,stop)
                    if (end!=stop or stats.get('nonconstant_sign_offsets',0)
                        or states[stop][25]!=mask or kind!='success'):
                        continue
                    d=next((d for d in null[stop] if ((d>>1)&delta).bit_count()&1),None)
                    if d:
                        row['solutions'].append(dict(start=start,end=stop,seed=q,delta=delta,decode=d,**stats))
                        break
            if len(row['solutions'])>=10:
                break
        paths.append(row)
    return paths

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--extend',type=int,default=40)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    n,d,refs=annotate(ops)
    peaks=groups(n,46)
    w,m=physical_trace(ops)
    print('peaks',len(peaks),'cuts',sum(b-a+1 for a,b in peaks),'largest',sorted(peaks,key=lambda r:-r[1]+r[0])[:10],flush=True)
    answer=find(ops,n,d,refs,peaks,w,m,args.extend)
    print('solved',sum(bool(x['solutions']) for x in answer),'coverage',sum(x['length'] for x in answer if x['solutions']),flush=True)
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,peaks=len(peaks),results=answer),indent=2)+'\n')

if __name__=='__main__':
    main()
