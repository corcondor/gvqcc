#!/usr/bin/env python3
"""Independent small-circuit controls for exact phase-aware fanout discovery."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import re
import subprocess

import kickmix as km


def parse(line):
    return line.split()[0], tuple(map(int, re.findall(r'\bq(\d+)\b', line)))


def run(lines, x, n=7):
    q=[x>>i&1 for i in range(n)];phase=0
    for line in lines:
        op,w=parse(line)
        if op=='X':q[w[0]]^=1
        elif op=='CX':q[w[1]]^=q[w[0]]
        elif op=='CCX':q[w[2]]^=q[w[0]]&q[w[1]]
        elif op in ('Z','CZ','CCZ'):
            value=1
            for v in w:value&=q[v]
            phase^=value
        else:raise ValueError(line)
    return q,phase


def patch(lines, candidate):
    a,b,t,u=candidate['qubits'];removed=set(candidate['remove_phase_ops'])
    added={}
    for correction in candidate['corrections']:
        assert correction['condition']==-1
        qs=correction['qubits'];op={1:'Z',2:'CZ',3:'CCZ'}[len(qs)]
        added.setdefault(correction['before_source_op'],[]).append(op+' '+ ' '.join(f'q{q}' for q in qs))
    out=[]
    for i,line in enumerate(lines):
        out+=added.get(i,[])
        if i==candidate['first'] or i in removed:continue
        if i==candidate['second']:
            assert candidate['condition']==-1
            out += [f'CX q{t} q{u}',f'CCX q{a} q{b} q{t}',f'CX q{t} q{u}']
        else:out.append(line)
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scanner',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    cases=[
      ('free_z',['CCX q0 q1 q2','Z q2','CCX q0 q1 q3'],-1),
      ('free_cz_overlap',['CCX q0 q1 q2','CZ q0 q2','CCX q0 q1 q3'],-1),
      ('cancel_ccz',['CCX q0 q1 q2','CZ q2 q4','CCZ q0 q1 q4','CCX q0 q1 q3'],-2),
      ('commuting_target_write',['CCX q0 q1 q2','X q2','Z q2','CCX q0 q1 q3'],-1),
      ('paid_correction',['CCX q0 q1 q2','CZ q2 q4','CCX q0 q1 q3'],None),
      ('quartic',['CCX q0 q1 q2','CCZ q2 q4 q5','CCX q0 q1 q3'],None),
      ('target_used',['CCX q0 q1 q2','CX q2 q4','Z q2','CCX q0 q1 q3'],None),
      ('control_changed',['CCX q0 q1 q2','X q0','Z q2','CCX q0 q1 q3'],None),
      ('guard_changed',['HMR q6 b0','CCX q0 q1 q2 if b0','Z q2','BIT_INVERT b0','CCX q0 q1 q3 if b0'],None),
      ('branch_boundary',['HMR q6 b0','CCX q0 q1 q2','PUSH_CONDITION if b0','Z q2','POP_CONDITION','CCX q0 q1 q3'],None),
    ]
    records=[];columns=0
    for name,lines,delta in cases:
        kmb=a.out/f'{name}.kmb';km.Circuit('\n'.join(lines)+'\n').to_file(kmb,format='kmb')
        jp=a.out/f'{name}.json';subprocess.run([str(a.scanner),str(kmb),str(jp)],check=True)
        result=json.loads(jp.read_text());assert result['candidate_count']==(0 if delta is None else 1),(name,result)
        count=0
        if delta is not None:
            c=result['candidates'][0];assert c['delta_toffoli']==delta
            new=patch(lines,c)
            n=max(q for l in lines for q in parse(l)[1])+1
            for x in range(1<<n):assert run(lines,x,n)==run(new,x,n);count+=1
            columns+=count
            assert sum(parse(l)[0] in ('CCX','CCZ','CSWAP') for l in new)-sum(parse(l)[0] in ('CCX','CCZ','CSWAP') for l in lines)==delta
        records.append(dict(name=name,expected_delta=delta,candidates=result['candidate_count'],exact_dirty_basis_phase_columns=count,kmb_sha256=hashlib.sha256(kmb.read_bytes()).hexdigest()))
    report=dict(status='PASS',controls=len(records),exact_dirty_basis_phase_columns=columns,records=records,
                scanner_sha256=hashlib.sha256(a.scanner.read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.out/'controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
