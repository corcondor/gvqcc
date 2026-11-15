#!/usr/bin/env python3
"""Bind the shortlisted phase experiments to the exact public v27 circuit.

Requires the KMX exported from the pinned public KMB and the first search's
full-domain finalists.  No circuit rewrite or official-shot verification.
"""
import json,hashlib
from pathlib import Path
import numpy as np
import invsqrt_next_phase_search as m

def main():
    root=Path(__file__).resolve().parent
    public=root.parent/'inputs/public_v27/invsqrt.kmb'
    pin='1ba197b027713aac164056d12505c87f286c3fcd94f403c522073325763bf2f9'
    assert hashlib.sha256(public.read_bytes()).hexdigest()==pin
    old_desc,old_bits=m.load('finalists')
    selected=[(d['line']+13,d['qubit']) for d in old_desc if d['kind']=='candidate']
    m.SOURCE=root/'invsqrt_next_public_v27.kmx'
    kmx_pin='c48666ae3a566096b026fc6b249ce8b15785f33db7fdc696308eccec79115720'
    assert hashlib.sha256(m.SOURCE.read_bytes()).hexdigest()==kmx_pin
    desc,bits=m.extract('public_finalists',range(1,m.N+1),selected=selected)
    assert len(desc)==len(old_desc)
    records=[]
    for i,(a,b) in enumerate(zip(old_desc,desc)):
        assert a['kind']==b['kind']
        if a['kind']=='rotation':assert a['half_turns']==b['half_turns']
        equal=bool(np.array_equal(old_bits[i],bits[i]));assert equal,(i,a,b)
        records.append({'feature':i,'kind':a['kind'],'old_line':a.get('line'),'public_line':b.get('line'),'qubit':a.get('qubit'),'equal_on_all_inputs':equal})
    report={'status':'EXACT_BOOLEAN_FEATURE_BINDING_PASS','source_public_kmb_sha256':pin,'source_public_kmx_sha256':kmx_pin,'kmx_export':'KickMix Circuit.from_file(exact public KMB).to_file(format=kmx)','inputs':m.N,'features':records,'scope':'All 38 original rotation predicates, 10 shortlisted added predicates, and all-zero-HMR parity match the previously evaluated cache circuit. Angles are unchanged. This binds those numerical search results; it does not certify every measurement branch or earlier discarded candidates.'}
    (root/'invsqrt_next_public_v27_feature_binding.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='features'}))

if __name__=='__main__':main()
