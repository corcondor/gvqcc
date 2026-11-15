"""Emit exact local width-gauge paths in the baseline and report measured coverage."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

import kickmix as km
import numpy as np

from gauge_probe import MAX_X, SOURCE_SHA, advance, columns, gate, physical_trace, propagate
from peak_probe import snapshots

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--peaks',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    raw=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,raw))
    small,mask=physical_trace(ops)
    plans=json.loads(args.peaks.read_text())
    assert plans['source']==SOURCE_SHA
    rows=plans['results']
    possible=[(r,h) for r in rows for h in r['solutions']
              if not h.get('sign_offsets') and not h.get('hmr_offsets')]
    positions={h[k] for r,h in possible for k in ('start','end')}
    whole,one=snapshots(ops,np.arange(1,MAX_X+1,dtype=np.uint32),positions)
    small_marker=(1<<63)-1
    by=defaultdict(list)
    fresh=max(int(i) for l in raw for i in re.findall(r'\bb(\d+)\b',l))+1
    last=-1
    choices=[]
    for r,h in possible:
        a,b=h['start'],h['end']; f=h['decode']
        q=h['seed']; d=h['delta']
        if a<last or whole[a][25]!=small_marker or whole[b][25]!=small_marker:
            continue
        z=one if f&1 else 0
        controls=[j for j in range(46) if f>>(j+1)&1]
        assert 25 not in controls
        for j in controls:
            z^=whole[b][j]
            if d>>j&1:
                z^=small_marker
        if z!=small_marker:
            continue
        end,final,status,extras=propagate(ops,small,mask,1<<q,a,b)
        assert end==b and status=='success' and final==d and not extras
        assert all(25 not in qs for _,qs in ops[a:b])
        tag=f'b{fresh}';fresh+=1
        by[a]+=[f'CX q25 q{q}',f'HMR q25 {tag}']
        if f&1:
            by[b].append('X q25')
        by[b]+=[f'CX q{j} q25' for j in controls]
        by[b]+=[f'CX q25 q{j}' for j in range(46) if d>>j&1]
        by[b].append(f'Z q25 if {tag}')
        choices.append(dict(**h,peak_cuts=r['length']))
        last=b
    lines=[]
    for i,line in enumerate(raw):
        lines+=by[i]
        lines.append(line)
    assert choices
    c=km.Circuit('\n'.join(lines)+'\n')
    assert c.num_qubits==46 and c.operation_statistics().num_toffoli_like==1550
    path=args.out.with_suffix('.kmb')
    c.to_file(path,format='kmb')
    receipt=dict(source=SOURCE_SHA, candidate=hashlib.sha256(path.read_bytes()).hexdigest(),
                 all_inputs=MAX_X,local_coverage=sum(r['peak_cuts'] for r in choices),
                 regions=len(choices),circuits_cost_improvement=None,choices=choices)
    args.out.write_text(json.dumps(receipt,indent=2)+'\n')
    print({k:v for k,v in receipt.items() if k!='choices'},flush=True)

if __name__=='__main__':
    main()
