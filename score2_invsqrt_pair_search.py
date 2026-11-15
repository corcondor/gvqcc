#!/usr/bin/env python3
"""Reproduce the two bounded four-AND searches with two extra live inputs."""
import json
from pathlib import Path
from score_invsqrt_joint_synthesis import synth

def main():
    base=Path(__file__).parent
    for a,b in [(17,28),(17,16)]:
        table=json.loads((base/f'score2_invsqrt_pair{a}_{b}_table.json').read_text())
        print(json.dumps({'starting_pair':[a,b],'patterns':len(table['rows'])}),flush=True)
        result=synth(table,4,60,29);result.update(extra_pair=[a,b],reachable_patterns=len(table['rows']))
        (base/f'score2_invsqrt_pair{a}_{b}_sat.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)

if __name__=='__main__':main()
