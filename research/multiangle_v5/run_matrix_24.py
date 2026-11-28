#!/usr/bin/env python3
"""24 fixed research screens; no speculative/unbounded RREF run variants.

All tests build actual MeasuredCircuit gate sequences in memory, execute
all valid addresses and each symbolic HMR phase coefficient. KMX is emitted
separately for nominated winners, not for every screen.
"""
import argparse,hashlib,json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--seeds',type=Path,required=True,help='directory with four named research NPZ seeds')
 ap.add_argument('--out',type=Path,required=True,help='fresh experiment directory; no overwrite')
 ap.add_argument('--max-workers',type=int,default=3)
 a=ap.parse_args()
 if a.out.exists():raise FileExistsError('append-only: choose a fresh output dir')
 a.out.mkdir(parents=True)
 seeds=['c46_public_v8.npz','C45_B129_JACOBI_OPTIMIZED.npz',
        'c45_B130_postangle_PSD_physical_pass.npz',
        'c45_B130_postangle_PSD_physical_pass_coupled_numeric_only.npz']
 cases=[(seed,axis,sup) for seed in seeds for axis in ('fixed-upper','fixed-lower') for sup in (2,3,8)]
 def run(case):
  seed,axis,sup=case
  name=f'{Path(seed).stem}_{axis}_s{sup}'
  cmd=[sys.executable,str(HERE/'high_group_basis.py'),
      '--seed',str(a.seeds/seed),'--out',str(a.out/name),
      '--axis',axis,'--max-support',str(sup),
      '--global-mode','canonical']
  cp=subprocess.run(cmd,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'},capture_output=True,text=True)
  (a.out/(name+'.stdout')).write_text(cp.stdout)
  (a.out/(name+'.stderr')).write_text(cp.stderr)
  if cp.returncode:raise RuntimeError((name,cp.returncode,cp.stderr[-500:]))
  summary=json.loads((a.out/name/'summary.json').read_text())
  summary.update(run_id=name,source_sha256=hashlib.sha256((a.seeds/seed).read_bytes()).hexdigest(),
                 native_KickMix=False)
  return summary
 results=[]
 with ThreadPoolExecutor(max_workers=a.max_workers) as pool:
  for f in as_completed([pool.submit(run,case) for case in cases]):
   x=f.result();results.append(x)
   print(json.dumps({k:x[k] for k in ('run_id','CCX','CX','Q')}),flush=True)
 results.sort(key=lambda x:x['run_id'])
 with (a.out/'matrix.jsonl').open('w') as f:
  for x in results:f.write(json.dumps(x,sort_keys=True)+'\n')
 print('RUNS',len(results))

if __name__=='__main__':main()
