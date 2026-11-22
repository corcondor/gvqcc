"""Correct the small number of temporal tag breaks in a 7-bit candidate.

The reference word table remains unchanged. Every repaired candidate is
numerically reverified against FeMoCo. No KMB matching is inferred.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from griffith_qcc.chemistry import helper_report
from griffith_qcc.physics import evaluate_factorization


def repair(parent, candidate, reference, out_dir):
    out_dir.mkdir(parents=True,exist_ok=True)
    with np.load(parent,allow_pickle=False) as z:old=z['angle_words']
    with np.load(candidate,allow_pickle=False) as z:data={k:z[k].copy() for k in z.files}
    word=data['angle_words'].copy()
    hits=[]
    for a in range(len(word)):
        for j in range(5):
            orig=((int(word[a,j])>>5)^(int(word[a,j])>>6))&1
            for k in range(1,15):
                idx=5*k+j
                tag=((int(word[a,idx])>>5)^(int(word[a,idx])>>6))&1
                if tag!=orig:
                    hits.append([a,idx,int(word[a,idx]),int(old[a,idx])])
    fixes=[]
    for a,idx,_,_ in hits:
        if int(word[a,idx]) == int(old[a,idx]):
            raise AssertionError('cannot repair non-parent modified tag without changing base')
    for label,index_set in [('all',range(len(hits)))] + [(f'one_{i}',[i]) for i in range(len(hits))]:
        w=word.copy()
        for i in index_set:
            a,idx,_,repl=hits[i];w[a,idx]=repl
        newdata=data.copy();newdata['angle_words']=w
        path=out_dir/f'repaired_{label}.npz'
        np.savez_compressed(path,**newdata)
        m=evaluate_factorization(path,reference)
        h=helper_report(w)
        fixes.append({'name':label,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
           'physics':m,'helper_violations':h['helper_time_invariance_violations']})
    report={'parent_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),
            'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'changed_cells':hits,'cases':fixes,'official_score':None}
    (out_dir/'repair_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'num_helpers_broken':len(hits),'results':[{'name':x['name'],'error_1':x['physics']['error_1'],
            'error_2':x['physics']['error_2'],'pass':x['physics']['passes_physical_gates'],
            'helper_violations':x['helper_violations']} for x in fixes]},indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    x=p.parse_args()
    repair(x.parent,x.candidate,x.reference,x.output)
