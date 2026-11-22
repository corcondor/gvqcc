#!/usr/bin/env python3
"""Global address-dependent sign gauge search driven by real compiled KMB Toffoli cost.

For each 11-bit Walsh parity selector, reframe ALL 1219x75 ANGLE words, exact-proof
of the sign vector, compile real measured-feedback KMB. The first bank screens
candidates; final full three-bank checks are symbolic XOR+all-HMR-phase proofs.
This does NOT independently validate KickMix or score a full 18-file entry.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
try:
    from gauge5_exact import transform as gauge_transform, decode
except ImportError:
    from gauge5_ci import fix as gauge_transform, decode


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parity(addr, mask):
    ret=np.zeros(len(addr),dtype=np.uint8)
    for bit in range(11):
        if mask & (1<<bit):
            ret ^= ((addr >> bit) & 1).astype(np.uint8)
    return ret


def execute(command, path, env):
    started=time.monotonic()
    p=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
    Path(path).write_text(p.stdout)
    if p.returncode:
        raise RuntimeError(f'Command failed rc={p.returncode}: {command}; see {path}\n{p.stdout[-2000:]}')
    return round(time.monotonic()-started,3)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--masks',default='1,16,128,257,1024,2047',help='comma separated bitsets (decimal)')
    p.add_argument('--keep-finalists',type=int,default=2)
    p.add_argument('--include-topbit-xor',action='store_true')
    p.add_argument('--compiler',type=Path,default=Path(__file__).with_name('compile_gauge_partial.py'))
    p.add_argument('--verifier',type=Path,default=Path(__file__).with_name('verify_exact_ir.py'))
    a=p.parse_args()
    out=a.out;out.mkdir(parents=True,exist_ok=True)
    with np.load(a.source,allow_pickle=False) as z:
        arrays={k:z[k].copy() for k in z.files}
    words=arrays['angle_words'].astype(np.uint8)
    edges=arrays['tree_edges'].astype(np.int64)
    assert words.shape==(1219,75)
    orig=decode(words,edges)
    adr=np.arange(len(words),dtype=np.uint16)
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
    records=[]
    variants=[('baseline',0,False)]
    for m in [int(x,0) for x in a.masks.split(',') if x.strip()]:
        if m<=0 or m>=2048: raise ValueError(f'Bad mask {m}')
        variants.append((f'walsh_{m:04x}',m,False))
        if a.include_topbit_xor: variants.append((f'walsh_topbit_{m:04x}',m,True))
    for label,mask,top in variants:
        sigma=parity(adr,mask)
        if top:
            sigma ^= (words[:,0]>>6)&1
        if label=='baseline':patched=words.copy();distinct=0;matrix_count=0
        else:patched,matrix_count=gauge_transform(words,edges,sigma);distinct=int(np.count_nonzero(patched!=words))
        err=float(np.max(np.abs(decode(patched,edges)-orig*(1-2*sigma.astype(np.int16))[:,None])))
        if err>1e-13: raise AssertionError((label,err))
        folder=out/label;folder.mkdir(parents=True,exist_ok=True)
        npz=folder/'source.npz'; np.savez_compressed(npz,**{**arrays,'angle_words':patched})
        dest=folder/'bank0';dest.mkdir(exist_ok=True)
        cmd=[sys.executable,str(a.compiler),'--source',str(npz),'--out',str(dest),
             '--banks','1','--start','0','--mode','signed6resid','--lowbits','4','--J','5','--trials','1']
        elapsed=execute(cmd,folder/'bank0_compile.log',env)
        compiled=json.loads((dest/'build_report.json').read_text())
        t=int(compiled['T']);q=int(compiled['maxQ'])
        record=dict(name=label,selector_mask=mask,topbit_xor=top,changed_words=distinct,
                    output_vector_err=err,constraint_matrix_variants=matrix_count,
                    NPZ_sha256=sha(npz),bank0_T=t,bank0_Q=q,bank0_time=elapsed,
                    bank0_kmb_sha256=sha(dest/'angle_k_0.kmb'))
        records.append(record)
        print(label,'bank0',t,'Q',q,'changed',distinct,'time',elapsed,flush=True)
    by={r['name']:r for r in records}
    finalists=['baseline']+[r['name'] for r in sorted(records[1:],key=lambda r:(r['bank0_T'],r['name']))[:a.keep_finalists]]
    for name in finalists:
        f=out/name;npz=f/'source.npz';dest=f/'bank3';dest.mkdir(exist_ok=True)
        cmd=[sys.executable,str(a.compiler),'--source',str(npz),'--out',str(dest),
             '--banks','3','--start','0','--mode','signed6resid','--lowbits','4','--J','5','--trials','1']
        by[name]['bank3_seconds']=execute(cmd,f/'bank3_compile.log',env)
        verify=f/'bank3_exact.json'
        execute([sys.executable,str(a.verifier),'--source',str(npz),'--circuits',str(dest),'--banks','3','--J','5','--out',str(verify)],f/'bank3_verify.log',env)
        proof=json.loads(verify.read_text()); assert proof['all_pass'] and proof['banks']==3
        by[name]['bank3_T']=int(proof['total_pass_T'])
        by[name]['bank3_Q']=int(proof['maxQ'])
        by[name]['bank3_exact_phase_dirty_and_scratch']=True
        by[name]['bank3_kmb_SHA256']=[item['sha256'] for item in proof['bank_results']]
        print('FULL3',name,'T',by[name]['bank3_T'],'Q',by[name]['bank3_Q'],flush=True)
    report=dict(method='GF2_affine_global_sign_field_compiler_feedback',source_sha256=sha(a.source),
                mask_candidates=len(records)-1,first_bank_all_compiled=True,
                verified_finalists=finalists,records=records,
                native_KickMix_executed=False,full15_KMB_executed=False,official_score=None)
    (out/'signfield_cost_search.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'finalists':finalists,'bank0':{x['name']:x['bank0_T'] for x in records},'baseline_bank3':by['baseline']['bank3_T']},indent=2))

if __name__=='__main__':main()