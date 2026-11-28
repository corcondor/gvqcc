from pathlib import Path
import json
p=json.load(open('plan.json'))
b=[(r[1],r[2]) for l in open('extracted2.tsv') if (r:=list(map(int,l.split())))]
out={}
for site in p:
 i=int(site); lo,hi=b[i]; after=hi+1
 out[site]=[after,after+16,after+128,after+1024]+([b[i+1][0],b[i+1][1]+1] if i+1<len(b) else [])
Path('futureplan.json').write_text(json.dumps(out))
Path('future_landmarks.txt').write_text(''.join(f'{x}\n' for x in sorted({x for k in out.values() for x in k})))
