#!/usr/bin/env python3
"""Independent legality/expected-output check of newly captured default failures.

Does not classify the decoder's internal failure cause.
"""
import hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent

def mul(a,b):
    z=0
    while b:
        if b&1:z^=a
        b>>=1;a<<=1
        if a&4096:a^=0x1053
    return z
EXP=[];x=1
for _ in range(4095):EXP.append(x);x=mul(x,2)
assert x==1 and len(set(EXP))==4095

def main():
    records=[]
    for batch in (158,261):
        folder=HERE/f'default_failure_batch{batch}';receipt=json.loads((folder/'capture_receipt.json').read_text())
        for record in receipt['captures']:
            path=folder/record['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'];d=np.load(path,allow_pickle=False);pos=list(map(int,d['error_positions']));vals=list(map(int,d['error_values']));weight=int(d['weight']);assert len(pos)==len(vals)==weight<=35 and len(set(pos))==weight and all(0<=p<4095 for p in pos) and all(1<=v<4096 for v in vals)
            want=[]
            for j in range(70):
                s=0
                for p,v in zip(pos,vals):s^=mul(v,EXP[((j+1)*p)%4095])
                want.append(s)
            assert want==list(map(int,d['syndromes']));wantphase=sum((v&int(d['mbuc'][p])).bit_count() for p,v in zip(pos,vals))&1;assert wantphase==bool(d['phase'])
            dif=sum((int(a)^int(b)).bit_count() for a,b in zip(d['syndromes'],d['actual_syndromes']));assert dif==record['syndrome_error_bits'] and int(d['actual_ancillas'].sum())==record['dirty_ancilla_bits'];assert bool(d['phase'])!=bool(d['actual_phase'])
            records.append(dict(file=str(path.relative_to(HERE)),weight=weight,all_70_syndromes_recomputed=True,expected_phase_recomputed=True,unique_legal_positions=True,all_nonzero_values=True,syndrome_error_bits=dif,dirty_ancilla_bits=0,sha256=record['sha256'],failure_cause_classified=False))
    result=dict(status='PASS_INDEPENDENT_CAPTURE_LEGALITY_AND_EXPECTED_OUTPUT',GF12_modulus='0x1053',primitive_element=2,cases=records,relationship_to_inherited_kappa3257_case='Not investigated; these are additional regression fixtures.')
    (HERE/'default_failure_fixtures_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()