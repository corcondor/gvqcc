"""Fail closed. A verifier PASS with one phase error is still rejected."""
from pathlib import Path
import json,sys
p=Path(sys.argv[1])
load=lambda s:json.loads(Path(str(p)+s+'.json').read_text())
raw,dist,structured=[load(s) for s in ('.raw','.distribution','.structured')]
capt=load('.captured'); official=load('.official'); salt=load('.salt')
for a,n in [(raw,996),(dist,1024),(structured,432)]:
    assert a['shots']==n
    assert not any(a[k] for k in ('value','phase','dirty','mask')),a.get('failures',[])[:3]
assert sum(x['shots'] for x in capt['panels'].values())==1024
assert all(not any(x['errors']) for x in capt['panels'].values())
for a in (official,salt):
    assert a['status']=='PASS' and a['verified_shots']==102400
    assert a['value_errors']==a['phase_errors']==0
    assert a['num_qubits']<=900
    assert a['circuit_sha256']==raw['sha256']==dist['sha256']==structured['sha256']==capt['sha256']
# This only certifies tested shots, not a universal circuit proof.
assert all(a['toffoli_count']<316000 for a in (official,salt)), '316k mean-cost gate not met'
print('NATIVE REGRESSION + COST GATE PASSED; all-domain Lean refinement remains separate')
