import json
from pathlib import Path
from collections import Counter
p=json.load(open('plan.json'))
all_intervals={}
for site,(pre,post,last1,last2,last3,now) in p.items():
    if now-pre<=100000:
        all_intervals[site]=[[pre,now]]
    else:
        all_intervals[site]=[[pre,post],[last1,now]]
Path('intervals.json').write_text(json.dumps(all_intervals))
b=sorted(x for spans in all_intervals.values() for x in spans)
merged=[]
for lo,hi in b:
    if merged and merged[-1][1]>=lo: merged[-1][1]=max(merged[-1][1],hi)
    else: merged.append([lo,hi])
Path('intervals.txt').write_text(''.join(f'{l} {h}\n' for l,h in merged))
print(len(merged),sum(h-l for l,h in merged),len(b))
