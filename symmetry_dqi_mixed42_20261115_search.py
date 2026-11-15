#!/usr/bin/env python3
"""Bounded search from two GF4 mixed-place interpolation orbit representatives."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from theory_bilinear_prepare import evaluate, gf_mul

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--driver',type=Path,required=True)
    ap.add_argument('--breadth',action='store_true')
    ap.add_argument('--output-dir',type=Path)
    args=ap.parse_args()
    root=Path(__file__).parent;data=json.loads((root/'symmetry_dqi_mixed42_20261115_inputs.json').read_text())
    output_dir=args.output_dir or root;output_dir.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();records=[]
    # PGL2(GF4) acts on the six degree-two places in two orbits of size ten
    # on 3-subsets. Sample one site-configuration representative of each.
    # This is not a proof that all decompositions are equivalent after the
    # fixed GF4096 quotient/output map is included; 18 starts remain unsearched.
    starts=([(n,202611151000+n) for n in range(20) if n not in (0,2)] if args.breadth
            else [(0,202611150001),(2,202611150002)])
    paths,growth,budget=(8,12,90) if args.breadth else (128,8,165)
    for number,seed in starts:
        rec=data['records'][number];source=Path(rec['input_file'])
        assert hashlib.sha256(source.read_bytes()).hexdigest()==rec['input_sha256']
        output=output_dir/f'symmetry_dqi_mixed42_20261115_orbit{number}.json'
        assert not output.exists()
        command=[str(args.driver),str(source),str(output),str(paths),'1000000','1000',str(growth),str(seed)]
        process=subprocess.run(command,capture_output=True,text=True,check=True,timeout=max(1,budget-(time.monotonic()-start)))
        result=json.loads(output.read_text());terms=result['best_terms']
        for i in range(12):
            for j in range(12):assert evaluate(terms,1<<i,1<<j)==gf_mul(1<<i,1<<j)
        record={'initial_record':number,'quadratic_orbits':rec['quadratic_orbits'],'input_sha256':rec['input_sha256'],
                'command':command,'stdout':process.stdout.strip(),'result':result,'independent_best_basis_checks':144}
        records.append(record);print(json.dumps({k:v for k,v in result.items() if k not in ('best_terms','rank_histogram')}),flush=True)
        if result['best_rank']<42:break
    summary={'status':'COMPLETE','target':'GF(2^12) multiplication, exact DQI821 coordinate system','original_rank':42,
             'best_rank':min(x['result']['best_rank'] for x in records),'initial_family':'GF4 degree6 mixed rational/quadratic places',
             'new_family_factor_lines':23,'installed_GF8_family_factor_lines':28,'time_budget_seconds':budget,
             'initial_starts_searched':len(records),'initial_starts_available':20,
             'PGL2_scope':'Classification of evaluation-site sets only; equivalence of full fixed-coordinate decompositions is not asserted',
             'records':records,'seconds':time.monotonic()-start,'production_circuit_modified':False,
             'scope':'Finite constructive search, not a minimum-rank proof. Different initial family established by invariant line count.'}
    name='symmetry_dqi_mixed42_20261115_breadth.json' if args.breadth else 'symmetry_dqi_mixed42_20261115_search.json'
    (output_dir/name).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)

if __name__=='__main__':main()
