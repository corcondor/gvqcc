"""Cascaded, independent OpenEvolve evaluator for existing 15 ANGLE loaders.

This *is not* the official competition verifier. A numerical improvement requires
full independent phase proof and later the unchanged official Kickmix evaluator.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,sys,time,zipfile,copy,subprocess,tempfile
from pathlib import Path
from exact_angle import verify,run,N
from kmb_v2 import load,Gate,Circuit

THIS=Path(__file__).resolve().parent
DEFAULT_INPUT=THIS/'inputs'
BASE_CHEM_COST=294887890.976471
BASE_T=14722
BASE_L=4030
BASE_Q=427
BASE_INV_COST=78673.55534364567
BASE_DQI_COST=359707293756.04297
REF_INV=2076774.233715282
REF_DQI=24439463583672.93
REF_CHEM=3355599588.3155375
BASE_SCORE=27.327844395957978
VALID_OPS={'X','CX','CCX','R','HMR','CZ_IF'}

def baseline():
    root=Path(os.environ.get('GVQCC_ANGLE_BASELINE',DEFAULT_INPUT))
    circuits=[load(root/f'angle_k_{k}.kmb') for k in range(15)]
    check,expected=verify(circuits)
    assert check.ccx==BASE_L,('Expected SCORE10 4030 loader family',check.ccx)
    return circuits,expected

def compare(old:list[Circuit],new:list[Circuit]):
    if len(new)!=15:raise ValueError('15 circuits required')
    for i,(a,b) in enumerate(zip(old,new)):
        if b.nqubits>128 or b.nqubits<51:raise ValueError(f'loader {i} exceeds qubit contract')
        if a.registers!=b.registers:raise ValueError('changed public register contract')
        if a.nbits!=b.nbits or a.tags!=b.tags:raise ValueError('changed classical register metadata')
        if any(g.name not in VALID_OPS for g in b.ops):raise ValueError('unknown or prohibited instruction')
        if any(any(q<0 or q>=b.nqubits for q in g.q) for g in b.ops):raise ValueError('quantum operand out of bounds')
        if any(any(x<0 or x>=b.nbits for x in g.bit+g.cond) for g in b.ops):raise ValueError('classical operand out of bounds')
        if any(g.cond and g.name!='CZ_IF' for g in b.ops):raise ValueError('unsupported condition')
    return sum(g.name=='CCX' for c in new for g in c.ops)

def calculate_score(loader_ccx:int,qubits:int=BASE_Q)->tuple[float,float]:
    # Only valid for SAME original Givens words, same R/B/C and full state-prep layout.
    chem_cost=BASE_CHEM_COST*(6662+2*loader_ccx)/BASE_T*(qubits/BASE_Q)
    score=((REF_INV/BASE_INV_COST)*(REF_DQI/BASE_DQI_COST)*(REF_CHEM/chem_cost))**(1/3)
    return score,chem_cost

def evaluate(program_path:str,save_to=None):
    t0=time.perf_counter()
    old,reference=baseline()
    info={'source':str(program_path),'baseline_loader_ccx':BASE_L,'baseline_local_score':BASE_SCORE}
    try:
        with tempfile.TemporaryDirectory(prefix='gvqcc_candidate_') as tempdir:
            output=Path(tempdir)/'out'
            input_dir=Path(os.environ.get('GVQCC_ANGLE_BASELINE',DEFAULT_INPUT)).resolve()
            child_env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('TOKEN','SECRET','PASSWORD','API_KEY','CREDENTIAL','AUTH','COOKIE'))}
            result=subprocess.run([sys.executable,str(THIS/'worker.py'),str(Path(program_path).resolve()),str(input_dir),str(output)],
                                  cwd=str(THIS),capture_output=True,text=True,timeout=90,env=child_env)
            if result.returncode:
                raise RuntimeError('candidate generation failed: '+result.stderr[-1000:])
            proposed=[load(output/f'angle_k_{k}.kmb') for k in range(15)]
        t=compare(old,proposed)
        info['proposed_loader_ccx']=t
        if t>BASE_L:
            return {'combined_score':0.0,'valid':0,'error':'worse than baseline',**info}
        if t==BASE_L and all(x.ops==y.ops and x.nqubits==y.nqubits for x,y in zip(old,proposed)):
            info.update(status='BASELINE_UNCHANGED',reason='no change',verified=True,score=BASE_SCORE)
            return {'combined_score':1.0,'valid':1,'toffoli_savings':0,**info}
        # Independent exact checker, not the candidate module's own oracle.
        receipt,_=verify(proposed,reference=reference)
        score,chem=calculate_score(t)
        if t==BASE_L:score=BASE_SCORE
        free_baseline=sum(g.name in {'X','CX'} for c in old for g in c.ops)
        free_new=sum(g.name in {'X','CX'} for c in proposed for g in c.ops)
        info['free_gate_savings']=free_baseline-free_new
        info.update(status='EXACT_REACHABLE_PASS',verified=True,toffoli_savings=BASE_L-t,
                    score=score,chemistry_cost=chem,output_digest=receipt.outputs_digest,
                    proof_cases=receipt.transitions,measurement_variables=receipt.measurement_phases)
        if save_to and t<BASE_L:
            out=Path(save_to);out.mkdir(parents=True,exist_ok=True)
            for i,c in enumerate(proposed):c.write(out/f'angle_k_{i}.kmb')
            (out/'proof.json').write_text(json.dumps(info,indent=2)+'\n')
        return {'combined_score':score/BASE_SCORE,'valid':1,**info}
    except Exception as e:
        info.update(status='REJECTED',error=f'{type(e).__name__}: {e}')
        return {'combined_score':0.0,'valid':0,**info}
    finally:
        info['elapsed_seconds']=time.perf_counter()-t0

def evaluate_stage1(program_path):
    return evaluate(program_path)

def evaluate_stage2(program_path):
    return evaluate(program_path)

def main():
    p=argparse.ArgumentParser();p.add_argument('program',nargs='?',default=str(THIS/'candidate.py'))
    p.add_argument('--save-to');args=p.parse_args()
    result=evaluate(args.program,save_to=args.save_to)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if not result['valid']:raise SystemExit(1)
if __name__=='__main__':main()
