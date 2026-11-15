#!/usr/bin/env python3
"""Bounded shortened-interval refinement of score_invsqrt_retire.

Ends are fixed arithmetic region boundaries, not every instruction. Full-domain
truth tables certify any positive one-product identity. Negative results cover
only a left parity of at most two current wires, as explicitly reported.
"""
import hashlib
import json
from pathlib import Path
import random
import time
import score_invsqrt_retire as r


def main():
    began=time.monotonic();base=Path(__file__).parent
    path=base/'invsqrt_structural_e46.kmx'
    lines,ops=r.instructions(path);masks,depth,peaks,intervals=r.scan(lines,ops)
    boundaries=[2889,3319,4409,7573,8566,14884,16795,17198,19763,20557]
    selected=[]
    for end in boundaries:
        while depth[end]:end+=1
        eligible=[]
        for item in intervals:
            if item['q'] in range(22,26) or not item['start']<end<=item['end']:continue
            covered=[p for p in item['covered'] if p<end]
            if not covered:continue
            eligible.append(dict(q=item['q'],start=item['start'],end=end,
                                 old_end=item['end'],covered=covered))
        eligible.sort(key=lambda x:-len(x['covered']))
        selected+=eligible[:3]
    by_end={}
    for item in selected:by_end.setdefault(item['end'],[]).append(item)
    print(json.dumps({'panel_size':len(selected),'fixed_boundaries':boundaries}),flush=True)
    domain,vals=r.initial_values();stack=[];rng=random.Random(1215846)
    samples=list(range(1,257))+[2**k+d for k in range(3,22) for d in range(-2,3)]+[rng.randrange(1,r.MAX_X+1) for _ in range(512)]
    results=[]
    for i,(op,qs) in enumerate(ops):
        for item in by_end.get(i,[]):
            t=time.monotonic();identity=r.one_product(vals,item['q'],domain,samples)
            result={**item,'identity':identity,'seconds':time.monotonic()-t}
            results.append(result)
            print(json.dumps({k:v for k,v in result.items() if k!='covered'}),flush=True)
        if op=='PUSH_CONDITION':stack.append(vals[:])
        elif op=='POP_CONDITION':before=stack.pop();assert vals==before;vals=before
        else:r.advance(op,qs,vals,domain)
    report={'status':'COMPLETE','baseline_kmx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'legal_inputs':r.MAX_X,'scope':'one product; left factor is parity of at most two live wires, right arbitrary affine parity; linear remainder arbitrary',
            'fixed_boundaries':boundaries,'tested':results,'accepted':sum(x['identity'] is not None for x in results),
            'elapsed_seconds':time.monotonic()-began}
    (base/'score_invsqrt_short_retire.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tested'}))


if __name__=='__main__':main()
