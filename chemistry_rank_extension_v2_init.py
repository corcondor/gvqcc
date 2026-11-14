"""Create a C45 initial factor with exact fixed one-body contributions.

The new column has d=H2_I-sum(W)=0. Its nonnegative squared amplitude
minimizes the exact two-body residual within the eight screened directions.
This creates numerical slack for a subsequent full refit; it does not by
itself claim a lower resource score.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'))
    directions=np.load(ROOT/'gvqcc_repo/chemistry_rank_extension_v2.npz')['directions'][:,:-1]
    directions/=np.linalg.norm(directions,axis=1)[:,None]
    m=FixedAngles(base)
    linear=np.einsum('ri,rij,rj->r',directions,m.A,directions)
    gram=np.empty((m.R,m.R))
    for r in range(m.R):
        for s in range(m.R):
            gram[r,s]=(directions[r]@m.G4[r,s]@directions[s])**2
    def objective(p):return 2*linear@p+p@gram@p,2*linear+2*gram@p
    opt=minimize(objective,np.zeros(m.R),jac=True,method='L-BFGS-B',bounds=[(0,None)]*m.R,options={'maxiter':1000,'ftol':1e-15,'gtol':1e-12,'maxls':40})
    w=base['W'];ii=base['H2_I'];r,b,c=w.shape
    rows=[]
    for fraction in (0.25,0.5,1.0):
        amplitudes=np.sqrt(fraction*opt.x)
        neww=np.concatenate((w, (amplitudes[:,None]*directions)[:,:,None]),axis=2)
        newi=np.concatenate((ii,neww[:,:,-1].sum(axis=1)[:,None]),axis=1)
        data=dict(base);data['W']=neww;data['H2_I']=newi
        path=ROOT/'gvqcc_repo'/('chemistry_rank_extension_v2_init_'+str(fraction).replace('.','p')+'.npz')
        np.savez_compressed(path,**data)
        exact=evaluate_dfthc_angle_words(data['angle_words'],neww,newi-neww.sum(axis=1),m.S,m.beta,m.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
        predicted=(m.e20+objective(fraction*opt.x)[0])**.5
        row={'fraction':fraction,'amplitudes':amplitudes.tolist(),'predicted_error_2':float(predicted),'official_numerical_metrics':exact,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'angle_words_unchanged':bool(np.array_equal(base['angle_words'],data['angle_words'])),'shape':list(neww.shape),'full_circuit_verified':False}
        rows.append(row);print(json.dumps(row),flush=True)
    report={'scope':'C45 initializer only; exact official numerical reevaluation; no claim of better total cost or full circuit PASS','optimizer_success':bool(opt.success),'optimizer_termination':str(opt.message),'amplitude_squared_solution':opt.x.tolist(),'quadratic_linear':linear.tolist(),'quadratic_gram':gram.tolist(),'candidates':rows}
    (ROOT/'gvqcc_repo/chemistry_rank_extension_v2_init.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
