#!/usr/bin/env python3
"""Check whether a fitted candidate still passes with original one-body words.

The separate first N angle rows affect only error_1, not Lambda/E_gap/error_2.
This check separates a useful numeric refit from a necessary loader-table change.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    source=dict(np.load(a.source,allow_pickle=False));baseline=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz',allow_pickle=False))
    n=len(source['tree_edges'])+1
    assert np.array_equal(source['tree_edges'],baseline['tree_edges'])
    dd={k:np.array(v,copy=True) for k,v in source.items()};dd['angle_words'][:n]=baseline['angle_words'][:n]
    m=FastFixedAngles(dd)
    mm=evaluate_dfthc_angle_words(dd['angle_words'],dd['W'],dd['H2_I']-dd['W'].sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=dd['tree_edges'],energy_upper=UPPER_ENERGY)
    passed=bool(mm['error_1']<=.02 and mm['error_2']<=.02 and mm['Lambda']>49 and mm['E_gap']>3.914898 and mm['gap_in_domain'] and np.isfinite(mm['lambda_eff']))
    path=a.out/'restored.npz';np.savez_compressed(path,**dd)
    result={'source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidate':str(path),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'restored_onebody_words':int(np.sum(source['angle_words'][:n]!=baseline['angle_words'][:n])),'remaining_changed_words_vs_baseline':int(np.sum(dd['angle_words']!=baseline['angle_words'])),'official_numeric_metrics':mm,'numerical_pass':passed,'W_and_H2_I_unchanged_vs_source':True,'full_circuit_verified':False,'seconds':time.monotonic()-start}
    (a.out/'restore_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
