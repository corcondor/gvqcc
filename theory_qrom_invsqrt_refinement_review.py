#!/usr/bin/env python3
"""Small independent-oracle review of the actual affine refinement function.

Extracts only affine_match from the reviewed source via AST. Compares its
answer with exhaustive coefficient enumeration, including severe signature
collisions. This does not rerun the large inverse-root circuit.
"""
import ast
import hashlib
import itertools
import json
from pathlib import Path
import random


def main():
    root=Path(__file__).parent;source=root/'theory_invsqrt_reachable.py'
    body=ast.parse(source.read_text())
    run=next(n for n in body.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    fn=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='affine_match')
    module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
    code=compile(module,str(source),'exec')
    rng=random.Random(20261115);domain=126;sample=[1,4]
    totals={'queries':0,'member_targets':0,'nonmember_targets':0,'counterexample_refinements':0,'max_refinements':0}
    for trial in range(12):
        values=[rng.randrange(64)<<1 for _ in range(5)]
        eligible=list(range(4));excluded={4}
        signatures=[sum(((v>>x)&1)<<i for i,x in enumerate(sample)) for v in values]
        generators=[domain]+[values[q] for q in eligible]
        exact_span={0}
        for g in generators:exact_span|={v^g for v in list(exact_span)}
        for target6 in range(64):
            target=target6<<1
            stats={'queries':0,'counterexample_refinements':0,'max_refinements':0,'witness_inputs':[]}
            env=dict(values=values,domain=domain,sample=sample,sigmask=3,signatures=signatures,
                     max_terms=46,MAX_X=6,lineno=trial,affine_decisions=stats)
            exec(code,env)
            signature=sum(((target>>x)&1)<<i for i,x in enumerate(sample))
            answer=env['affine_match'](target,signature,excluded)
            assert (answer is not None)==(target in exact_span)
            if answer is not None:
                constant,controls=answer;result=domain if constant else 0
                assert not set(controls)&excluded
                for q in controls:result^=values[q]
                assert result==target
                totals['member_targets']+=1
            else:totals['nonmember_targets']+=1
            totals['queries']+=1
            totals['counterexample_refinements']+=stats['counterexample_refinements']
            totals['max_refinements']=max(totals['max_refinements'],stats['max_refinements'])
    report={'status':'PASS_EXHAUSTIVE_SMALL_COEFFICIENT_ORACLE',
            'reviewed_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'inputs':6,'signature_inputs':sample,'generator_sets':12,
            'arbitrary_targets_per_generator_set':64,'totals':totals,
            'scope':'Actual affine_match function against full coefficient enumeration on small truth tables, with deliberate signature collisions; no large circuit rerun.'}
    output=root/'theory_qrom_invsqrt_refinement_review.json'
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
