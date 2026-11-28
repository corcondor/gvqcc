#!/usr/bin/env python3
"""Recreate and verify the complete 61,750,702-op DQI candidate from exact V111."""
from pathlib import Path
import argparse, hashlib, json, subprocess
import numpy as np
ROOT=Path(__file__).resolve().parent
SOURCE_SHA='7182b05e1a4d0bc568de33e463259fcdab29daba61369b6e3d0d52185716d8e2'
CANDIDATE_SHA='733ec803e325a52e1fba323de4898dcd852d606a517e62bb757892a74829886f'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()
def run(command,output):
    result=subprocess.run([str(x) for x in command],capture_output=True,text=True,check=True)
    parsed=json.loads(result.stdout);parsed['command']=[str(x) for x in command]
    Path(output).write_text(json.dumps(parsed,indent=2)+'\n');return parsed
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output-directory',type=Path,required=True);a=p.parse_args();assert sha(a.baseline)==SOURCE_SHA
    w=a.output_directory.resolve();w.mkdir(parents=True,exist_ok=True)
    for name in ['patch_dqi_joint','check_dqi_joint','sim_dqi_joint','audit_shear_entry']:
        subprocess.run(['g++','-std=c++17','-O2',str(ROOT/f'{name}.cpp'),'-o',str(w/name)],check=True)
    data=np.load(ROOT/'dqi_64_legal_inputs.npz');inp=w/'inputs64.txt'
    with inp.open('w') as f:
        for prefix,A in [('S',data['syndromes']),('E',data['mbuc'])]:
            assert A.shape[0]==64
            for j in range(A.shape[1]):
                for b in range(12):f.write(f'{prefix}{j} {b} {sum((int(x)>>b&1)<<i for i,x in enumerate(A[:,j]))}\n')
        f.write('P 0 '+str(sum(int(x)<<i for i,x in enumerate(data['phase'])))+'\n')
    assert sha(inp)=='426b92a1b9f1a24e4da4966be366c4c9e530f3d144c5f1c7a350bc32e4d97d1e'
    out=w/'dqi.kmb';mapping=w/'hmr_ids.txt';journal=ROOT/'dqi_selected_journal.txt'
    results={}
    results['clean_entry']=run([w/'audit_shear_entry',a.baseline],w/'clean_entry.json')
    results['build']=run([w/'patch_dqi_joint',a.baseline,journal,out,mapping],w/'build.json');assert sha(out)==CANDIDATE_SHA
    results['stream']=run([w/'check_dqi_joint',a.baseline,out,journal],w/'stream.json')
    results['full64']=run([w/'sim_dqi_joint',a.baseline,out,inp,11220261127,mapping],w/'full64.json')
    results.update(status='COMPLETE_REPRODUCTION_PASS',source_sha256=SOURCE_SHA,candidate_sha256=CANDIDATE_SHA,candidate_path=str(out),official_verifier=False,global_qubits=900)
    (w/'receipt.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:results[k] for k in ['status','candidate_path','candidate_sha256','global_qubits','official_verifier']}))
if __name__=='__main__':main()