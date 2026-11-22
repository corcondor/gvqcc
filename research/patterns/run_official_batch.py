#!/usr/bin/env python3
"""Batch official scoreinfra PHYSICS ONLY, shared FCIDUMP context for reproducibility.
Not the native KickMix verifier; no actual Toffoli/gate cost is assessed.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from structural_pattern_library import apply,load_npz,sha256

def run(cases,verifier_root):
    root=Path(verifier_root)
    sys.path.insert(0,str(root.resolve()))
    from dfthcsos.scoreinfra.reference import load_reference,load_fixed_shifts,PACKAGED_FCIDUMP,UPPER_ENERGY
    from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words,symmetric_from_lower
    ref=load_reference(PACKAGED_FCIDUMP)
    shifts=load_fixed_shifts()
    shas={str(p):sha256(root/'dfthcsos'/p) for p in ['scoreinfra/dfthc_math.py','scoreinfra/reference.py','FeMoCo76o113e.fixed_shifts.npz','FeMoCo76o113e.fcidump']}
    out=[]
    for case in cases:
        base=load_npz(Path(case['seed']))
        z=base if case['action'].get('type')=='identity' else apply(base,case['action'])
        z.update(shifts)
        S=symmetric_from_lower(z['Hsym_lower'],ref['orbitals'])
        beta=float(z['H1_I'])-.5*float(np.trace(S))
        W0=z['H2_I']-z['W'].sum(axis=1)
        m=evaluate_dfthc_angle_words(z['angle_words'],z['W'],W0,S,beta,ref,
          brot=int(z.get('brot',7)),tree_edges=z['tree_edges'],energy_upper=UPPER_ENERGY)
        keys=['error_1','error_2','Lambda','E_gap','lambda_eff','gap_in_domain']
        metrics={k:(bool(m[k]) if k=='gap_in_domain' else float(m[k])) for k in keys}
        passed=metrics['error_1']<=.02 and metrics['error_2']<=.02 and metrics['Lambda']>49 and metrics['E_gap']>3.914898 and metrics['gap_in_domain'] and np.isfinite(metrics['lambda_eff'])
        event={'case':case['case'],'seed_sha256':sha256(case['seed']),'action':case['action'],'official_scoreinfra_metrics':metrics,'strict_physics_pass':bool(passed),'verifier_source_sha256':shas,'evidence':'OFFICIAL_SCOREINFRA_PHYSICS_ONLY','native_KickMix_test':None,'official_score':None}
        event['event_id']=hashlib.sha256(json.dumps({k:event[k] for k in ['case','seed_sha256','action']},sort_keys=True).encode()).hexdigest()
        out.append(event)
        print(json.dumps({'case':case['case'],'pass':bool(passed),'error_1':metrics['error_1'],'E_gap':metrics['E_gap']}),flush=True)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cases',type=Path,required=True)
    ap.add_argument('--verifier-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    events=run(json.loads(a.cases.read_text()),a.verifier_root)
    a.out.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in events))
if __name__=='__main__':main()
