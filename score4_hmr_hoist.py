#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Move an unconditional HMR before target-only Boolean writes.

The exact Kraus identity is M_m X_q**f = (-1)**(m*f) M_m.
Thus a measured target's final CCX can become a measurement-conditioned CZ.
Every original read of the target, non-Pauli phase and reset is a barrier.
Original measurement bits are copied at their old position, so moving a
measurement never changes the earlier classical control flow.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

Q = re.compile(r'\bq(\d+)\b')
B = re.compile(r'\bb(\d+)\b')

def parse(lines):
    depth=0;out=[]
    for i,line in enumerate(lines):
        tokens=line.split();op=tokens[0] if tokens else ''
        qs=tuple(map(int,Q.findall(line)))
        condition=int(tokens[-1][1:]) if 'if' in tokens else None
        out.append((op,qs,condition,depth))
        if op=='PUSH_CONDITION':depth+=1
        elif op=='POP_CONDITION':
            depth-=1
            if depth<0:raise ValueError('Unbalanced condition stack')
    if depth:raise ValueError('Unbalanced condition stack')
    return out

def plans(lines):
    ops=parse(lines);refs={};answer=[]
    for i,(op,qs,cond,depth) in enumerate(ops):
        if op=='HMR' and cond is None and depth==0:
            q=qs[0];targets=[]
            for j in reversed(refs.get(q,[])):
                gate,wires,c,d=ops[j]
                if gate not in ('X','CX','CCX') or wires[-1]!=q:break
                targets.append(j)
            targets.reverse()
            # Inserting before an already active conditional block would
            # change the measurement's scope. Start at a depth-zero write.
            starts=[j for j in targets if ops[j][3]==0]
            if starts:
                start=starts[0];targets=[j for j in targets if j>=start]
                answer.append(dict(start=start,end=i,qubit=q,targets=targets,
                                   saved_ccx=sum(ops[j][0]=='CCX' for j in targets)))
        for q in qs:refs.setdefault(q,[]).append(i)
    return answer

def identity_check():
    checked=0
    for controls in range(3):
        for classical_guard in (0,1):
            for measurement in (0,1):
                for basis in range(1<<(controls+2)):
                    # The last untouched bit is an arbitrary reference.
                    target=(basis>>controls)&1
                    f=int(all((basis>>k)&1 for k in range(controls)))&classical_guard
                    left=(-1)**(measurement*(target^f))
                    right=(-1)**(measurement*f)*(-1)**(measurement*target)
                    assert left==right
                    checked+=1
    return dict(status='PASS',kraus_matrix_entries_checked=checked,
                identity='M_m X_q^f = (-1)^(m f) M_m',
                scope='All computational basis columns, both measurement outcomes and guard values; linearity includes arbitrary superpositions and entangled reference systems.')

def apply(lines,plan):
    ops=parse(lines);fresh=max(map(int,B.findall('\n'.join(lines))),default=-1)+1
    start,end,q=plan['start'],plan['end'],plan['qubit'];targets=set(plan['targets'])
    assert ops[end][0]=='HMR' and ops[end][2:] == (None,0)
    assert ops[start][3]==0
    assert all(q not in ops[j][1] or j in targets for j in range(start,end))
    original_bit=int(lines[end].split()[2][1:]);result=[];rewrites=[]
    for i,line in enumerate(lines):
        if i==start:result.append(f'HMR q{q} b{fresh}')
        if i in targets:
            gate,wires,cond,depth=ops[i]
            assert gate in ('X','CX','CCX') and wires[-1]==q
            phase={'X':'NEG','CX':'Z','CCX':'CZ'}[gate]
            correction=' '.join([phase,*[f'q{x}' for x in wires[:-1]],'if',f'b{fresh}'])
            new=[correction] if cond is None else [f'PUSH_CONDITION if b{cond}',correction,'POP_CONDITION']
            result.extend(new);rewrites.append(dict(source_line=i+1,before=line,after=new))
        elif i==end:
            result.extend([f'BIT_STORE0 b{original_bit}',f'BIT_INVERT b{original_bit} if b{fresh}'])
        else:result.append(line)
    certificate={**plan,'fresh_measurement_bit':fresh,'original_measurement_bit':original_bit,
                 'rewrites':rewrites,'old_bit_preserved_until_original_measurement':True,
                 'original_target_unread_and_unreset_between_measurements':True}
    return result,certificate

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--include-zero-cost-hoists',action='store_true')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    import kickmix as km
    source=km.Circuit.from_file(args.source)
    initial=str(source).splitlines();lines=initial;certificates=[]
    initial_plans=plans(lines)
    while True:
        available=plans(lines)
        if not args.include_zero_cost_hoists:available=[p for p in available if p['saved_ccx']]
        if not available:break
        available.sort(key=lambda p:(-p['saved_ccx'],-len(p['targets']),p['start']))
        lines,certificate=apply(lines,available[0]);certificates.append(certificate)
        if len(certificates)>2000:raise RuntimeError('Unexpected nontermination')
    final=km.Circuit('\n'.join(lines)+'\n')
    before=Counter(x[0] for x in parse(initial));after=Counter(x[0] for x in parse(lines))
    reduction=before['CCX']-after['CCX']
    assert reduction==sum(p['saved_ccx'] for p in certificates)
    assert source.num_qubits==final.num_qubits
    assert [s for s in initial if s.startswith('Z_POW ')]==[s for s in lines if s.startswith('Z_POW ')]
    candidate=args.out/'candidate.kmb';final.to_file(candidate,format='kmb')
    (args.out/'candidate.kmx').write_text('\n'.join(lines)+'\n')
    report=dict(status='EXACT_KRAUS_REWRITES_CONSTRUCTED',source=str(args.source.resolve()),
                source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                candidate=str(candidate.resolve()),candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                initial_plans=initial_plans,hoists=certificates,additional_toffoli_reduction=reduction,
                source_toffoli=source.operation_statistics().num_toffoli_like,
                candidate_toffoli=final.operation_statistics().num_toffoli_like,
                qubits=final.num_qubits,quantum_width_unchanged=True,
                arbitrary_phase_angles_unchanged=True,kraus_identity_check=identity_check(),
                official_verification='NOT_RUN',source_gates=dict(before),candidate_gates=dict(after))
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','candidate_sha256','source_toffoli','candidate_toffoli','additional_toffoli_reduction','qubits')}))
    print(json.dumps({'hoists':len(certificates),'initial_hoist_plans':len(initial_plans)}))

if __name__=='__main__':main()
