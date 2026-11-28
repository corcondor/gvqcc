"""Export exact #327 GF4-derived binary dictionaries for native all-tape compiler."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'dqi_rank96_f4'))
import certify
rows,_=certify.check()
allrows=[('original',i,t) for i,t in enumerate(certify.originals())]
for r,new,_ in rows:allrows.append((r['source'],r['type'],new))
with open(sys.argv[1],'w') as f:
    print(len(allrows),file=f)
    for name,i,ts in allrows:
        print(name,i,len(ts),file=f)
        for t in ts:print(*t,file=f)
