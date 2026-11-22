"""Run a fail-closed *candidate grid* of physics and local learned XAG.

This is a working co-evaluation loop, not a finished full 15-bank/physical
end-to-end gradient trainer. The adapter deliberately leaves native KMB cost
as unknown and refuses to infer a new leaderboard score from local witnesses.
"""
import argparse,hashlib,json
from pathlib import Path
from griffith_qcc.chemistry import helper_report,bank_delta_tables,load_words
from griffith_qcc.physics import evaluate_factorization
from griffith_qcc.joint import Physical,JointCandidate,candidate_record
from griffith_qcc.train import train_xag


def run(candidates,ref,out,*,trials=4,steps=250):
    report={'source':'Griffith-inspired original joint candidate grid',
            'full_native_cost_available':False,'competition_score_update':None,
            'scope':'REAL_PHYSICS_AND_LEARNED_LOCAL_XAG_NOT_FULL_COMPETITION'}
    report['candidates']=[]
    for path in candidates:
        obj={'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        p=evaluate_factorization(path,ref)
        obj['physical']=p
        w=load_words(path)
        obj['helper_contract']=helper_report(w)
        # The same logical cut is trained for every physical/gauge candidate;
        # if that cut changes, it must be trained and re-proven again.
        table=bank_delta_tables(w,high_block=0)[4][8]
        learned,trained=train_xag([table],num_inputs=4,products=1,
                                 trials=trials,steps=steps,lr=.12,
                                 seed=20261122,exact_warm_start=False)
        obj['neural_xag']={'hard_exact':learned is not None,
                           'local_products':None if learned is None else len(learned.products),
                           'hard_exact_restarts':sum(t['hard_bit_errors']==0 for t in trained['trials'])}
        # All numerical / proxy improvements must be separated from KMB.
        obj['joint_record']=candidate_record(JointCandidate(path.name,
            Physical(p['error_1'],p['error_2'],p['Lambda'],p['E_gap'],p['lambda_eff']),
            None, obj['sha256']))
        report['candidates'].append(obj)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,default=Path('joint_grid.json'))
    parser.add_argument('--trials',type=int,default=4)
    parser.add_argument('--steps',type=int,default=250)
    o=parser.parse_args()
    r=run(o.candidate,o.reference,o.output,trials=o.trials,steps=o.steps)
    print(json.dumps([{'candidate':v['filename'],'physical_pass':v['physical']['passes_physical_gates'],
         'lambda_eff':v['physical']['lambda_eff'],'helper_violations':v['helper_contract']['helper_time_invariance_violations'],
         'local_learned_exact':v['neural_xag']['hard_exact'] } for v in r['candidates']],indent=2))
