"""Use the full 70-word recurrence as a structural oracle, independent of mask."""
from collections import Counter
from diagnose import roots,F,read_capture,field_words,P,syndromes
import json
from pathlib import Path
FILES=['../old_capture.bin','../new_native_capture.bin']
p=[read_capture(f) for f in FILES]
def norm(p,a):
    d=len(p)-1
    return [F.mul(c,F.EXP[((i-d)*F.LOG[a])%4095]) for i,c in enumerate(p)]
def recurrence(p,s):
    from functools import reduce
    from operator import xor
    return all(not reduce(xor,(F.mul(x,y) for x,y in zip(p,s[j:])),0) for j in range(len(s)-len(p)+1))
out=Counter()
for s,x,y in zip(syndromes('../joint_work/audit/saved.bin'),*p):
    px,py=field_words(P,x),norm(field_words(P,y),2)
    truth=roots(F.forward(s)[0])-{0}
    bx,by=(truth <= roots(z) for z in (px,py))
    rx,ry=(recurrence(z,s) for z in (px,py))
    assert (bx,by)==(rx,ry)
    out[rx,ry]+=1
assert sum(out.values())==622
Path('../recurrence_audit.json').write_text(json.dumps({'columns':['old_pass','scale2_pass','count'],'counts':[[*k,n] for k,n in sorted(out.items())]},indent=2)+'\n')
print(out)
