"""Train + prove an XAG on genuine V8-derived subfunctions (not full loaders)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from griffith_qcc.chemistry import bank_delta_tables,load_words,helper_report
from griffith_qcc.xag import synthesize_shared_one_and,anf_nonlinear_terms
from griffith_qcc.kickmix_proof import prove_oracle
from griffith_qcc.train import train_xag


def run(v8:Path, output:Path, *, trials:int=8):
    words=load_words(v8)
    helpers=helper_report(words)
    out=output
    out.mkdir(exist_ok=True,parents=True)
    results={'input_sha256':hashlib.sha256(v8.read_bytes()).hexdigest(),
             'input_rows':len(words),'helper_contract':helpers,
             'scope':'EXACT_LOCAL_4BIT_NOT_A_V8_15BANK_KMB_PATCH',
             'official_kickmix_ran':False,'official_score_improvement':None}
    # A genuine V8 fourth-batch bank0 high slice with 5 ANF monomials,
    # learned as one AND with XOR/NOT readout. No hard seed is provided.
    f=bank_delta_tables(words,high_block=0)[4][8]
    learned,train=train_xag([f],num_inputs=4,products=1,trials=trials,steps=400,lr=.12,
                            seed=20261122,exact_warm_start=False)
    results['single_v8_output']={'bank':4,'bit':8,'high_address_block':0,'truth_table':hex(f),
                                 'anf_nonlinear_monomials':anf_nonlinear_terms(f,4),
                                 'learner_status':train['status'],
                                 'learner_hard_exact_trials':sum(t['hard_bit_errors']==0 for t in train['trials'])}
    if learned:
        kmx=learned.emit_kmx()
        cert=prove_oracle(kmx,4,1,expected_tables=(f,))
        (out/'v8_oneand_single.kmx').write_text(kmx)
        results['single_v8_output']['exact_kmx_proof']={k:v for k,v in cert.items() if k!='output_map'}
        results['single_v8_output']['learned_xag']=repr(learned)
        results['single_v8_output']['resources']=learned.resources()
    # Second example uses two different V8 ANGLE banks on the same four low
    # address bits. A single AND suffices for their combined Boolean function.
    delta=bank_delta_tables(words,high_block=3)
    a,b=delta[13][8],delta[14][4]
    independent=synthesize_shared_one_and([a,b],4)
    if independent is None: raise AssertionError('lost exact shared-AND witness on V8 data')
    c=prove_oracle(independent.emit_kmx(),4,2,expected_tables=(a,b))
    (out/'v8_oneand_crossbank_local.kmx').write_text(independent.emit_kmx())
    results['cross_bank_two_outputs']={
       'high_address_block':3,'banks':[13,14],'local_bits':[8,4],
       'packed_truth_tables':[hex(a),hex(b)],
       'naive_anf_nonlinear_monomials':anf_nonlinear_terms(a,4)+anf_nonlinear_terms(b,4),
       'exact_shared_products':len(independent.products),
       'exact_kmx_proof':{k:v for k,v in c.items() if k!='output_map'},
       'resource_estimate':independent.resources(),
       'warning':'Cross-bank sharing requires persistent circuit state not yet proven in the original 128Q loaders.'}
    (out/'local_search_receipt.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--v8',required=True,type=Path)
    parser.add_argument('--output',default='output_qcc_cut',type=Path)
    parser.add_argument('--trials',default=8,type=int)
    opts=parser.parse_args()
    run(opts.v8,opts.output,trials=opts.trials)
