#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Merge unconditional same-control Toffolis across disjoint measurements.

The earlier CCX is deferred, only if it commutes with EVERY crossed current
operation. Once adjacent, CCX(a,b,t); CCX(a,b,u) becomes
CX(t,u); CCX(a,b,t); CX(t,u). This is exact for arbitrary dirty targets.
All measurement and classical-control operations retain their original bytes.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import dqi_ccx_peephole as p
import kmb_profile as kp

SOURCE_SHA = '9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1'

def commute(first, other):
    assert first.opcode == 0x31 and first.condition is None
    base=other.opcode&127
    if base in (0x01,0x40,0x41,0x42):
        # The moved gate has no classical guard. Balanced stack scopes below
        # ensure it remains unconditional at the new location.
        return True
    if base in (0x12,0x50):
        return not set(first.qubits).intersection(other.qubits)
    return p.commutes_with_ccx(first,other)

def op_record(op):
    return dict(opcode=op.opcode,qubits=list(op.qubits),bit=op.bit,
                condition=op.condition,angle_hex=op.angle.hex(),source_index=op.source_index)

def coherent_identity_check():
    checked=0
    for mask in range(16):
        a,b,t,u=[(mask>>k)&1 for k in range(4)]
        before=(a,b,t^(a&b),u^(a&b))
        uu=u^t;tt=t^(a&b);uu^=tt
        after=(a,b,tt,uu)
        assert before==after
        checked+=1
    return dict(status='PASS',basis_columns=checked,phases='exactly +1 on both sides',
                implication='Identical permutation matrices on all 16 basis columns; equality extends linearly to every superposition and entangled reference.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path);ap.add_argument('discovery',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();profile=kp.profile(args.source,max_register_summaries=0)
    assert profile['raw_kmb_sha256']==SOURCE_SHA,'Unexpected baseline'
    discovery=json.loads(args.discovery.read_text())
    assert discovery['num_ops']==profile['header']['num_ops']
    opportunities=discovery['opportunities']
    endpoints=[r[k] for r in opportunities for k in ('first','second')]
    assert len(endpoints)==len(set(endpoints)),'Overlapping source endpoints'
    ranges=[]
    for item in sorted(opportunities,key=lambda x:x['first']):
        assert item['first_depth']==item['second_depth']==0
        assert item['first_condition']==item['second_condition']==-1
        if ranges and item['first']<ranges[-1][1]:ranges[-1][1]=max(ranges[-1][1],item['second']+1)
        else:ranges.append([item['first'],item['second']+1])
    circuit=p.BinaryCircuit(args.source,profile)
    certificates=[];splices=[];rejected=[]
    try:
        for start,end in ranges:
            prefix=circuit.opcodes[:start]
            assert prefix.count(0x81)==prefix.count(0x01),'Block begins inside conditional scope'
            original=list(circuit.operations(start,end));current=original[:]
            selected=[x for x in opportunities if start<=x['first'] and x['second']<end]
            edits={};steps=[]
            for item in selected:
                fi=next(i for i,o in enumerate(current) if o.source_index==item['first'])
                si=next(i for i,o in enumerate(current) if o.source_index==item['second'])
                first,second=current[fi],current[si]
                assert fi<si and first.opcode==second.opcode==0x31
                assert first.condition is second.condition is None
                assert set(first.qubits[:2])==set(second.qubits[:2])==set(item['controls'])
                assert first.qubits[2]!=second.qubits[2]
                depth=0
                for op in current[:si+1]:
                    if op is first or op is second:assert depth==0
                    if op.opcode==0x81:depth+=1
                    elif op.opcode==0x01:depth-=1;assert depth>=0
                assert depth==0
                middle=current[fi+1:si]
                bad=[op_record(o) for o in middle if not commute(first,o)]
                if bad:
                    rejected.append(dict(pair=item,noncommuting=bad));continue
                a,b,t=first.qubits;u=second.qubits[2]
                cx=p.Operation(0x21,(t,u))
                replacement=[cx,p.Operation(0x31,(a,b,t)),cx]
                current[fi:si+1]=middle+replacement
                edits[item['first']]=[];edits[item['second']]=replacement
                steps.append(dict(first_source_op=item['first'],second_source_op=item['second'],
                                  controls=[a,b],targets=[t,u],
                                  crossed_current_operations=len(middle),
                                  crossed_opcodes=dict(Counter(f'{o.opcode:02x}' for o in middle)),
                                  all_current_operations_commute=True,
                                  endpoints_unconditional=True,
                                  measurement_channel_commutation='Every crossed HMR/reset is disjoint from all three CCX wires.',
                                  identity='CCX(a,b,t); CCX(a,b,u) = CX(t,u); CCX(a,b,t); CX(t,u)'))
            # Recreate the edited block independently from original source IDs.
            expected=[new for op in original for new in edits.get(op.source_index,[op])]
            assert expected==current
            lookup={o.source_index:o for o in original}
            for index,after in sorted(edits.items()):
                splices.append((index,index+1,[lookup[index]],after))
            certificates.append(dict(start=start,end=end,rewrites=steps,
                                     before=[op_record(o) for o in original],
                                     after=[op_record(o) for o in current]))
        candidate=args.out/'dqi.kmb'
        p.write_rewritten(circuit,candidate,sorted(splices,key=lambda s:s[0]))
    finally:circuit.close()
    after=kp.profile(candidate,max_register_summaries=0)
    merges=sum(len(c['rewrites']) for c in certificates)
    assert merges>0
    assert profile['raw_gate_families']['CCX']['total']-after['raw_gate_families']['CCX']['total']==merges
    assert after['raw_gate_families']['CX']['total']-profile['raw_gate_families']['CX']['total']==2*merges
    assert profile['header']['num_qubits']==after['header']['num_qubits']
    assert profile['header']['num_bits']==after['header']['num_bits']
    report=dict(status='EXACT_LOCAL_REWRITES_PASS',source=str(args.source.resolve()),
                source_sha256=profile['raw_kmb_sha256'],candidate=str(candidate.resolve()),
                candidate_sha256=after['raw_kmb_sha256'],additional_unconditional_ccx_reduction=merges,
                added_cx=2*merges,qubits=after['header']['num_qubits'],
                classical_bits_unchanged=True,registers_and_measurements_copied_verbatim=True,
                quantum_width_unchanged=True,coherent_identity=coherent_identity_check(),
                blocks=certificates,rejected=rejected,official_verification='NOT_RUN',
                elapsed_seconds=time.monotonic()-started)
    (args.out/'rewrite_certificate.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.out/'before_profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (args.out/'after_profile.json').write_text(json.dumps(after,indent=2)+'\n')
    # Compact, deterministic edit recipe for rebuilding from the pinned source.
    recipe=dict(source_sha256=SOURCE_SHA,candidate_sha256=after['raw_kmb_sha256'],
                edits=[dict(index=s,old=op_record(before[0]),new=[op_record(o) for o in new])
                       for s,e,before,new in sorted(splices,key=lambda s:s[0])])
    (args.out/'patch.json').write_text(json.dumps(recipe,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('blocks','rejected')},indent=2))

if __name__=='__main__':main()
