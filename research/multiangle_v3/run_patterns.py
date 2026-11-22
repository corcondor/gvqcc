#!/usr/bin/env python3
"""Append-only per-run ledger: 9 HMR schedules + 4 affine + 4 affine/HMR.

Four real 7-bit/J5 NPZs x 15 slots. Every HMR branch is proved by independent
symbolic phase coefficients. Not a KickMix official pass or score.
"""
from __future__ import annotations
import argparse,hashlib,json,csv,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from hmr_patterns import ALGORITHMS as HMRS,compile_hmr,prove as prove_hmr
from affine_patterns import METHODS,synthesize_affine,hmr_from_reversible
from multi_angle_synthesis import prove as prove_plain,delta_table,sha256
ALGORITHMS=tuple(HMRS)+tuple(METHODS)+tuple(m+'--hmr-all-clean' for m in METHODS)

def compile_one(words,slot,method):
    if method in HMRS:
        c,s=compile_hmr(words,slot,method)
        return c,s,True
    if method.endswith('--hmr-all-clean'):
        base=method.split('--hmr-')[0]
        orig,stats=synthesize_affine(words,slot,base)
        c,s=hmr_from_reversible(orig,stats,'all-clean')
        return c,s,True
    c,s=synthesize_affine(words,slot,method)
    return c,s,False

def run(seeds,out,emit):
    out.mkdir(parents=True,exist_ok=False)
    if emit:(out/'kmx').mkdir()
    paths=[Path(__file__),Path(__file__).parent/'hmr_patterns.py',Path(__file__).parent/'affine_patterns.py',Path(__file__).resolve().parents[1]/'gvqcc_multiform'/'multi_angle_synthesis.py']
    scripts={p.name:sha256(p) for p in paths}
    groups={}
    ledger=out/'experiments.jsonl'
    records=0
    with ledger.open('w') as f:
      for source in seeds:
        with np.load(source,allow_pickle=False) as z:words=np.array(z['angle_words'],np.int64)
        seed_sha=sha256(source)
        for method in ALGORITHMS:
          agg=dict(source=source.name,method=method,slots=0,Q_peak=0,CCX=0,CX=0,X=0,HMR=0,conditional_CZ=0,phase_symbols_verified=0)
          for slot in range(15):
            circ,stat,measured=compile_one(words,slot,method)
            truth=delta_table(words,slot)
            proof=prove_hmr if measured else prove_plain
            for dirty in (7,314):
              cert=proof(circ,truth,dirty)
              assert cert['scratch_clean'] and cert['tags_unchanged']
              if measured:assert cert['all_HMR_phase_symbols_cancel']
            rid=hashlib.sha256(f'{seed_sha}|{method}|{slot}|{json.dumps(scripts,sort_keys=True)}'.encode()).hexdigest()
            rec=dict(schema='gvqcc.multiangle.v3.1',experiment_id=rid,
                method=method,slot=slot,source=source.name,source_sha256=seed_sha,
                compiler_source_sha256=scripts,
                qubits=int(stat['qubits']),CCX=int(stat['CCX']),CX=int(stat['CX']),X=int(stat.get('X',0)),
                HMR=int(stat.get('HMR',0)),conditional_CZ=int(stat.get('conditional_CZ',0)),
                valid_addresses=len(words),proof_all_addresses=True,dirty_target_seeds=[7,314],
                symbolic_all_measurement_phase_branches=bool(measured),
                native_KickMix_pass=False,official_score=None)
            if 'chosen_bases' in stat:rec['block_choices']=stat['chosen_bases']
            if 'HMR_active' in stat:rec['HMR_breakdown']={k:stat[k] for k in ('HMR_active','HMR_high','HMR_precomp')}
            if emit:
                target=out/'kmx'/source.stem/method/f'angle_k_{slot}.kmx'
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('w') as t:
                    for line in circ.kmx_lines():t.write(line+'\n')
                rec['kmx_path']=str(target.relative_to(out))
                rec['kmx_sha256']=sha256(target)
                rec['kmx_size_bytes']=target.stat().st_size
            f.write(json.dumps(rec,sort_keys=True,ensure_ascii=False)+'\n');f.flush()
            agg['slots']+=1;agg['Q_peak']=max(agg['Q_peak'],rec['qubits'])
            for item in ('CCX','CX','X','HMR','conditional_CZ'):agg[item]+=rec[item]
            agg['phase_symbols_verified']+=rec['HMR']
            records+=1
          agg['Q_times_CCX_proxy']=agg['Q_peak']*agg['CCX']
          groups[(source.name,method)]=agg
          print(f'{source.name} {method}: CCX={agg["CCX"]} Q={agg["Q_peak"]} HMR={agg["HMR"]}',flush=True)
    summary=dict(schema='gvqcc.multiangle.v3.1.summary',records=records,methods=list(ALGORITHMS),
                 sources=[p.name for p in seeds],source_script_hashes=scripts,
                 scope='exact all-address XOR and symbolic all-HMR phase proof; NO native KickMix real-input pass; NO score',
                 groups=sorted(groups.values(),key=lambda a:(a['source'],a['Q_times_CCX_proxy'],a['method'])))
    (out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    with (out/'comparisons.csv').open('w',newline='') as f:
      names=list(summary['groups'][0]);writer=csv.DictWriter(f,fieldnames=names)
      writer.writeheader();writer.writerows(summary['groups'])
    with (out/'SHA256SUMS').open('w') as f:
      for path in sorted(out.rglob('*')):
        if path.is_file() and path.name!='SHA256SUMS':f.write(f'{sha256(path)}  {path.relative_to(out)}\n')
    print('COMPLETE',records,'ALL_CHECKS_PASS',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--seeds',nargs='+',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--no-emit',action='store_true')
 a=p.parse_args();run(a.seeds,a.out,not a.no_emit)
