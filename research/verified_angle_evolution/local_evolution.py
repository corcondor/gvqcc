"""Offline seed-pool evaluation; for API-powered program mutation use OpenEvolve.

This DOES NOT claim to use an LLM without an API connection. Every evaluated
variant must pass the exact independent proof before it can be archived.
"""
from __future__ import annotations
import argparse, json,hashlib,time
from pathlib import Path
from evaluator import evaluate,BASE_SCORE
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'runs');p.add_argument('--programs',nargs='*',default=['candidate.py','candidate_free.py']);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    results=[]
    for path in a.programs:
        src=ROOT/path
        record=evaluate(str(src))
        record['source_sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
        record['actual_score_gain']=float(record.get('score',0))-BASE_SCORE if record.get('valid') else None
        results.append(record)
        with (a.output/'search.jsonl').open('a') as f:f.write(json.dumps(record,sort_keys=True)+'\n')
        print(json.dumps({'candidate':path,'valid':record.get('valid'),
                          'T_saved':record.get('toffoli_savings',0),
                          'free_saved':record.get('free_gate_savings',0),
                          'score':record.get('score',None)},ensure_ascii=False),flush=True)
    valid=[r for r in results if r['valid']]
    leader=max(valid,key=lambda r:(r['score'],r.get('free_gate_savings',0))) if valid else None
    summary={'status':'BOUNDED_LOCAL_SEARCH_FINISHED','tested':len(results),'valid':len(valid),
             'baseline_score':BASE_SCORE,'higher_scoring_candidate_found':bool(leader and leader['score']>BASE_SCORE+1e-9),
             'best':leader,'versions':results}
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
