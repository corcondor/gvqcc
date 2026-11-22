#!/usr/bin/env python3
"""Append-only v3 partition-width experiments: L=3,5,6, ANF and GF2 basis, plain and HMR."""
from __future__ import annotations
import argparse,hashlib,json,csv,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from partition_patterns import METHODS,compile_partition,convert_hmr
from hmr_patterns import prove as prove_hmr
from multi_angle_synthesis import prove as prove_plain,delta_table,sha256

def run(seeds,out,emit):
    out.mkdir(parents=True,exist_ok=False)
    (out/'kmx').mkdir(exist_ok=True)
    dirs={p.name:sha256(p) for p in [Path(__file__),Path(__file__).parent/'partition_patterns.py',Path(__file__).parent/'hmr_patterns.py',Path(__file__).resolve().parents[1]/'gvqcc_multiform'/'multi_angle_synthesis.py']}
    summ=[];count=0
    with (out/'experiments.jsonl').open('w') as log:
      for source in seeds:
        with np.load(source,allow_pickle=False) as z:words=np.array(z['angle_words'],np.int64)
        seedsha=sha256(source)
        for mode in METHODS:
            for hmr in (False,True):
                alg=mode+('--hmr-all-clean' if hmr else '')
                total=dict(source=source.name,method=alg,lowbits=int(mode[9]),Q_peak=0,CCX=0,CX=0,X=0,HMR=0,conditional_CZ=0,slots=0)
                for slot in range(15):
                    base,stat=compile_partition(words,slot,mode)
                    circ,st=convert_hmr(base,stat) if hmr else (base,stat)
                    delta=delta_table(words,slot)
                    certificate=prove_hmr if hmr else prove_plain
                    for seed in (7,314):
                        proof=certificate(circ,delta,seed)
                        assert proof['scratch_clean'] and proof['tags_unchanged']
                        if hmr:assert proof['all_HMR_phase_symbols_cancel']
                    cid=hashlib.sha256(f'{seedsha}|{alg}|{slot}|{json.dumps(dirs,sort_keys=True)}'.encode()).hexdigest()
                    rec=dict(schema='gvqcc.angle.partition.v3.1',experiment_id=cid,method=alg,slot=slot,source=source.name,source_sha256=seedsha,
                        script_sha256=dirs,CCX=int(st['CCX']),CX=int(st['CX']),X=int(st.get('X',0)),
                        qubits=int(st['qubits']),HMR=int(st.get('HMR',0)),conditional_CZ=int(st.get('conditional_CZ',0)),
                        exact_values_all_addresses=True,phase_all_HMR_symbols_zero=bool(hmr),
                        dirty_target_seeds=[7,314],valid_addresses=len(words),scratch_clean=True,
                        official_kickmix_verified=False,score_status='NOT_MEASURED')
                    if emit:
                        path=out/'kmx'/source.stem/alg/f'angle_k_{slot}.kmx'
                        path.parent.mkdir(parents=True,exist_ok=True)
                        with path.open('w') as f:
                            for line in circ.kmx_lines():f.write(line+'\n')
                        rec['kmx_sha256']=sha256(path)
                        rec['kmx_path']=str(path.relative_to(out))
                        rec['kmx_size_bytes']=path.stat().st_size
                    log.write(json.dumps(rec,sort_keys=True)+'\n');log.flush()
                    total['Q_peak']=max(total['Q_peak'],rec['qubits'])
                    total['slots']+=1
                    for k in ('CCX','CX','X','HMR','conditional_CZ'):total[k]+=rec[k]
                    count+=1
                total['Q_times_CCX_proxy']=total['Q_peak']*total['CCX']
                summ.append(total)
                print(f'{source.name} {alg} CCX={total["CCX"]} Q={total["Q_peak"]} HMR={total["HMR"]}',flush=True)
    summ.sort(key=lambda r:(r['source'],r['Q_times_CCX_proxy'],r['method']))
    (out/'summary.json').write_text(json.dumps(dict(records=count,groups=summ,scripts=dirs,methods=list(METHODS),schema='gvqcc.angle.partition.summary.v3.1',verification='bitparallel all legal addresses, independently phased all HMR branches; native KickMix NOT RUN'),indent=2)+'\n')
    with (out/'comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summ[0]));w.writeheader();w.writerows(summ)
    with (out/'SHA256SUMS').open('w') as f:
        for p in sorted(out.rglob('*')):
            if p.is_file() and p.name!='SHA256SUMS':f.write(f'{sha256(p)}  {p.relative_to(out)}\n')
    print('COMPLETE',count,'ALL_CHECKS_PASS',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seeds',required=True,nargs='+',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--no-emit',action='store_true');a=p.parse_args()
 run(a.seeds,a.out,not a.no_emit)
