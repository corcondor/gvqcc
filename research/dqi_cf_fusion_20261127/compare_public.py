"""Compare identical chart panels, not just reversible roundtrips."""
import sys,pathlib,json,numpy as np
base=pathlib.Path(sys.argv[1])
ref=json.loads((base/'ref/receipt.json').read_text())
labels=[x['label'] for x in ref['runs']['fwd']['cases']]
report={}
for mode in ('old','fixed','fused'):
    r=json.loads((base/mode/'receipt.json').read_text())
    details=[]
    for label in labels:
        a=np.load(base/'ref'/(label+'.npz'));b=np.load(base/mode/(label+'.npz'))
        same=(a['A']==b['A']).all(1)&(a['B']==b['B']).all(1)
        details.append({'label':label,'equal':int(same.sum()),'n':len(same)})
    report[mode]={'forward':details,'round':r['runs']['round']}
print(json.dumps(report,indent=2))
(base/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
for mode in ('fixed','fused'):
    assert all(x['equal']==x['n'] for x in report[mode]['forward']), (mode,'forward mismatch')
    assert all(x['clean']==x['n'] for x in report[mode]['round']['cases']), (mode,'unclean roundtrip')
