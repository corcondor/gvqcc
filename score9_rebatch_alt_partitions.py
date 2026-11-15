#!/usr/bin/env python3
"""Screen all Q<=128 complete-bank J=4 variable partitions on 1220 care rows.

Physical ANF coefficients whose masks are >=1220 vanish throughout the legal
address down-set. The canonical completion sets them to zero. The optimistic
cost drops every incompletely specified high column and is only a lower bound
inside the per-output paired-rank construction, not a circuit lower bound.
"""
from __future__ import annotations
import argparse,csv,hashlib,itertools,json,subprocess,time
from pathlib import Path
import numpy as np

REPO=Path(__file__).resolve().parent
ACTUAL_HASH='8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea'

def mobius(values):
    out=values.copy()
    for b in range(11):
        view=out.reshape(-1,1<<(b+1))
        view[:,1<<b:]^=view[:,:1<<b]
    return out

def deltas():
    words=np.load(REPO/'score8_chem_v27_recovered_words.npy',allow_pickle=False)
    assert words.shape==(1220,75) and hashlib.sha256(words.tobytes()).hexdigest()==ACTUAL_HASH
    words=np.pad(words,((0,0),(0,1)))
    return [words[:,4*k:4*k+4]^(words[:,4*k-4:4*k] if k else np.zeros((1220,4),np.uint8)) for k in range(19)]

def coefficients(delta):
    coded=delta.astype(np.uint32);coded^=(coded&64)<<1
    flat=np.zeros(2048,dtype=np.uint32)
    for j in range(4):flat[:1220]^=coded[:,j]<<(8*j)
    out=mobius(flat);out[1220:]=0
    # The legal address down-set makes truncation of these ANF coefficients
    # exact on all 1220 requested addresses, including the partial final row.
    assert np.array_equal(mobius(out)[:1220],flat[:1220])
    return out

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('/workspace/scratch/3815fb5fae06/score9_rebatch_alt'))
    a=parser.parse_args();a.out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    coeff=np.stack([coefficients(d) for d in deltas()]);binary=a.out/'coefficients.u32'
    coeff.astype('<u4').tofile(binary)
    exe=a.out/'partitions'
    subprocess.run(['g++','-O3','-std=c++17',str(REPO/'score9_rebatch_alt_partitions.cpp'),'-o',str(exe)],check=True)
    csvpath=a.out/'partitions.csv'
    with csvpath.open('w') as f:subprocess.run([str(exe),str(binary)],stdout=f,check=True)
    rows=[]
    with csvpath.open() as f:
        for row in csv.DictReader(f):
            row={key:([int(v) for v in value.split()] if key in ('ranks','completion_ranks') else int(value)) for key,value in row.items()}
            row['low_bits']=[b for b in range(11) if row['partition']>>b&1]
            rows.append(row)
    best={}
    for key in ('paired','joint_full','completion_paired','completion_joint','optimistic_paired'):
        chosen=[min((r for r in rows if r['batch']==k),key=lambda r:(r[key],r['qubits'],r['partition'])) for k in range(19)]
        best[key]={'loader_ccx':sum(r[key] for r in chosen),'max_qubits':max(r['qubits'] for r in chosen),'rows':chosen}
    fixed=[]
    for mask in sorted({r['partition'] for r in rows}):
        selected=[r for r in rows if r['partition']==mask]
        fixed.append({'partition':mask,'low_bits':selected[0]['low_bits'],'qubits':selected[0]['qubits'],**{key:sum(r[key] for r in selected) for key in best}})
    result=dict(status='COMPLETE_PARTITION_SCREEN',actual_words_sha256=ACTUAL_HASH,legal_addresses=1220,partitions=len(fixed),circuits_screened=len(rows),
                completion='All physical ANF masks >=1220 set to zero; such monomials vanish on every legal address.',
                method_scope='Complete low/high monomial banks, per-output paired-rank synthesis; joint_full additionally shares a rank2 correction between full odd-rank slices.',
                optimistic_scope='Dropping incomplete high columns is optimistic only for independent paired-rank synthesis under all completions, not general or joint synthesis.',
                exact_completion_scope='Greedy rank completion on nested specified-column prefixes is exact for each individual output matrix; it does not optimize joint multi-output products.',
                improvement_loader_threshold=4170,target28_loader_threshold=3643,best=best,best_fixed=sorted(fixed,key=lambda r:r['joint_full'])[:20],seconds=time.monotonic()-start)
    (a.out/'partitions.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ('best','best_fixed')}))
    for key,value in best.items():print(json.dumps({'method':key,'loader_ccx':value['loader_ccx'],'max_qubits':value['max_qubits'],'partitions':[r['partition'] for r in value['rows']]}))
    print(json.dumps({'best_fixed':result['best_fixed'][:5]}))

if __name__=='__main__':main()
