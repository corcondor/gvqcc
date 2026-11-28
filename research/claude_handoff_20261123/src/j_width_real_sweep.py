#!/usr/bin/env python3
"""Evaluate actual KMB CCX, Q, exact HMR phase for nonlocal J=3/4/5/6/7 groupings.

All 75 source Givens words stay invariant, only output-word grouping changes.
The first three banks across different J cover different numbers of words,
so cost-per-word is a FILTER, not a full 75-word comparison. Candidates require
official verifier/outer-loop rebuild before any score assertion.
"""
import os,sys,json,subprocess,hashlib,argparse
from pathlib import Path

def run(cmd, log, env):
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
    Path(log).write_text(r.stdout)
    if r.returncode:raise RuntimeError(f'{r.returncode}: {cmd}: {r.stdout[-1500:]}')

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--J-list',type=str,default='3,4,5,6,7')
p.add_argument('--banks',type=int,default=3)
p.add_argument('--compiler',type=Path,default=Path(__file__).with_name('compile_gauge_partial.py'))
p.add_argument('--verifier',type=Path,default=Path(__file__).with_name('verify_exact_ir.py'))
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
res=[]
for J in [int(x) for x in a.J_list.split(',')]:
    assert 2<=J<=8
    d=a.out/f'J{J}';d.mkdir(parents=True,exist_ok=True)
    run([sys.executable,str(a.compiler),'--source',str(a.source),'--out',str(d),'--J',str(J),'--banks',str(a.banks),'--mode','signed6resid','--lowbits','4','--trials','1'],d/'compile.log',env)
    run([sys.executable,str(a.verifier),'--source',str(a.source),'--circuits',str(d),'--J',str(J),'--banks',str(a.banks),'--out',str(d/'verify.json')],d/'verify.log',env)
    report=json.loads((d/'verify.json').read_text());assert report['all_pass']
    words=min(75,J*a.banks)
    item={'J':J,'num_banks':a.banks,'words_covered':words,'num_required_banks_for_75':(75+J-1)//J,
          'first_banks_T':report['total_pass_T'],'T_per_covered_word':report['total_pass_T']/words,
          'maxQ':report['maxQ'],'exact_value_phase_scratch':True,
          'kmb_sha256':[v['sha256'] for v in report['bank_results']]}
    res.append(item)
    print('J',J,'T',item['first_banks_T'],'Q',item['maxQ'],'T/word',item['T_per_covered_word'],flush=True)
obj={'kind':'J_REBLOCKING_75_WORDS_ACTUAL_KMB_EXACT_3BANK_TEST','source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'results':res,'native_KickMix':False,'full_75_word_comparison':False,'official_score':None,
 'limitation':'Different J groupings cover different numbers of words in the first three banks; T/word is a screening rate, not an official full-cost estimate.'}
(a.out/'J_reblock_comparison.json').write_text(json.dumps(obj,indent=2)+'\n')