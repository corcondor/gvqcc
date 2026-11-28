import json
from pathlib import Path
found=json.load(open('norm_relation_receipt.json'))['sites']
blocks=[(r[1],r[2]) for l in open('extracted2.tsv') if (r:=list(map(int,l.split())))]
assert len(blocks)==333
plan={}
for i,t,d,n,z,c in found:
 if d!=12 or t!=0: continue
 lo,hi=blocks[i]; p,q=blocks[i-1]
 plan[i]=[p,q+1,lo-1024,lo-128,lo-16,lo]
Path('plan.json').write_text(json.dumps(plan))
Path('landmarks.txt').write_text(''.join(f'{x}\n' for x in sorted({x for k in plan.values() for x in k})))
