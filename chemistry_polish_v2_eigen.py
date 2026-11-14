import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np,json
from pathlib import Path
from inverse_v2_chemistry_refit import FixedAngles
r=Path(__file__).resolve().parents[1];b=dict(np.load(r/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'));m=FixedAngles(b)
w=b['W'];d=b['H2_I']-w.sum(1);X=np.einsum('rbc,rbpq->rcpq',w,m.outer.reshape(m.R,m.B,m.N,m.N),optimize=True)
hp=m.hbase-np.einsum('rc,rcpq->pq',d,X);v=np.linalg.eigvalsh(hp)
print(json.dumps({'eigenvalues':v.tolist(),'min_abs':float(min(abs(v))),'min_gap':float(min(np.diff(v))),'num_lt_1e7':int(sum(abs(v)<1e-7))}),flush=True)
np.savez_compressed(r/'gvqcc_repo/chemistry_polish_v2_hprime.npz',hprime=hp,eigenvalues=v)
