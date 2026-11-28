"""Audit the exact KMB cut in 8-anchor; no locator splice is inferred."""
import json
from collections import Counter
from diagnose import F,P,field_words,read_capture,roots,syndromes,forney,projector

pan=list(syndromes('../../joint_work/audit/saved.bin'))
frames=read_capture('../d8capture.bin')
assert len(pan)==len(frames)==622
out=Counter()
for s,q in zip(pan,frames):
    p=field_words(P,q)
    canonical,v,*_=F.forward(s)
    expected=roots(canonical)-{0}
    observed={F.div(x,2) for x in roots(p) if x}
    miss=expected-observed;extra=observed-expected
    k=len(expected);out[k,len(miss),len(extra)]+=1
    if miss or extra:
        _,_,e=projector(p)
        assert len(e)<=35
    else:
        q=[F.mul(co,F.EXP[((i-(len(p)-1))*F.LOG[2])%4095]) for i,co in enumerate(p)]
        got=forney(q,s,observed)
        assert got=={x:F.ev(v,x) for x in expected}
result={'new_cut':128428359,'cases':622,'exact_support':sum(n for (w,m,e),n in out.items() if m==e==0),'lost_all_nonzero_roots':sum(n for (w,m,e),n in out.items() if m==w and m>0),'rows':[[*k,n] for k,n in sorted(out.items())]}
print(json.dumps(result,indent=2))
