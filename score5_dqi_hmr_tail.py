#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exactly turn the last two chart flag writes into HMR phase corrections.

Each target is untouched between its unconditional CCX and its unconditional
HMR. The fresh outcome is published to the original bit only at the original
HMR location. This preserves all prior uses/writes of the original bit.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import struct
import time
import dqi_ccx_peephole as P
import kmb_profile as K
from score4_measurement_fanout import op_record
from score4_dqi_guard_review import text as circuit_text

SOURCE = '6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02'


def encode(ops):
    columns={k:bytearray() for k in range(1,11)}
    for op in ops:
        assert op.opcode in (0x31,0x50,0xa0,0x40,0xc2)
        assert len(op.qubits)==((op.opcode>>4)&3)
        assert (op.bit is not None)==bool(op.opcode&0x40)
        assert (op.condition is not None)==bool(op.opcode&0x80)
        assert not op.angle
        columns[1].append(op.opcode)
        for k,q in zip(P.QUANTUM_COLUMNS[len(op.qubits)],op.qubits):
            columns[k].extend(struct.pack('<I',q))
        if op.bit is not None:columns[8].extend(struct.pack('<I',op.bit))
        if op.condition is not None:columns[9].extend(struct.pack('<I',op.condition))
    return {k:bytes(v) for k,v in columns.items()}


def write_edits(c,path,edits,num_bits):
    """Copy untouched KMB columns, checking all replaced original bytes."""
    splices={k:[] for k in range(1,12)}
    for lo,hi,old,new in edits:
        old_columns,new_columns=encode(old),encode(new)
        for k in range(1,11):
            a,b=c.column_range(k,lo,hi);offset=c.packets[k]['payload_offset']
            assert c.data[offset+a:offset+b]==old_columns[k]
            if old_columns[k]!=new_columns[k]:splices[k].append((a,b,new_columns[k]))
    sizes={k:p['payload_bytes']+sum(len(v)-(b-a) for a,b,v in splices[k])
           for k,p in c.packets.items()}
    header=dict(c.profile['header'],num_bits=num_bits)
    for field,k,width in [('num_ops',1,1),('num_ops_with_3_target_qubits',2,4),
        ('num_ops_with_2_target_qubits',5,4),('num_ops_with_1_target_qubits',7,4),
        ('num_ops_with_1_target_bit',8,4),('num_ops_with_1_condition_bit',9,4),
        ('num_ops_with_angle',10,16)]:header[field]=sizes[k]//width
    with path.open('xb') as f:
        f.write(K.HEADER.pack(K.MAGIC,*(header[x] for x in K.HEADER_FIELDS)))
        P.copy_range(c.data,f,K.HEADER.size,c.packets[1]['header_offset'])
        for k in range(1,12):
            packet=c.packets[k];offset=packet['payload_offset'];cursor=0
            f.write(K.PACKET.pack(k,sizes[k]))
            for a,b,new in splices[k]:
                assert a>=cursor
                P.copy_range(c.data,f,offset+cursor,offset+a)
                f.write(new);cursor=b
            P.copy_range(c.data,f,offset+cursor,offset+packet['payload_bytes'])


def identity():
    entries = 0
    for a,b,t,r,m,old_bit in itertools.product((0,1),repeat=6):
        original_phase = m * (t ^ (a & b)) % 2
        replacement_phase = (m*t + m*a*b) % 2
        assert original_phase == replacement_phase
        assert (a,b,0,r,m) == (a,b,0,r,0^m)
        entries += 1
    return dict(status='PASS', basis_outcome_classical_entries=entries,
                identity='M_m X_t^(a*b) = (-1)^(m*a*b) M_m',
                scope='Equal Kraus matrices separately for both outcomes, arbitrary target and reference. All intermediate instruments act as identity on this target and cannot read the fresh bit.')


def native_identity():
    import kickmix as km
    import numpy as np
    rng = np.random.default_rng(2026111561)
    qs = km.array([km.q(x) for x in range(4)])
    initial = rng.integers(0,2,(4,256),dtype=np.uint8).astype(bool)
    initial_bit = rng.integers(0,2,(1,256),dtype=np.uint8).astype(bool)
    original = km.Circuit('CCX q0 q1 q2\nHMR q2 b0\n')
    replacement = km.Circuit('HMR q2 b1\nCZ q0 q1 if b1\nBIT_STORE0 b0\nBIT_INVERT b0 if b1\n')
    outputs=[]
    for circuit in [original,replacement]:
        sim=km.Simulator(batch_size=256,seed=1562,debug_print=False)
        sim.write_across_shots(qs,initial)
        sim.write_across_shots(km.array([km.b(0)]),initial_bit)
        sim.do(circuit)
        outputs.append((sim.read_across_shots(qs),sim.read_across_shots(km.array([km.b(0)])),
                        sim.read_phase_flipped_across_shots()))
    assert all(np.array_equal(x,y) for x,y in zip(*outputs))
    return dict(status='PASS',shots=256,quantum_errors=0,classical_errors=0,phase_errors=0,
                scope='Native minimal instrument, with one HMR in each schedule. Full-interval random outcomes are not falsely paired by an unchanged RNG seed after measurement reordering.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('discovery',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    prof=K.profile(a.source,max_register_summaries=0)
    assert prof['raw_kmb_sha256']==SOURCE
    rows=json.loads(a.discovery.read_text())['candidates']
    assert len(rows)==2
    c=P.BinaryCircuit(a.source,prof);edits=[];proofs=[]
    try:
        previous_end=-1
        for number,row in enumerate(rows):
            lo,hi=row['start'],row['hmr'];q=row['target']
            assert previous_end<lo<hi
            assert row['writes']==[lo] and row['ccx_removed']==1
            assert c.opcodes[:lo].count(0x81)==c.opcodes[:lo].count(0x01)
            before=list(c.operations(lo,hi+1))
            first,last=before[0],before[-1]
            assert first.opcode==0x31 and first.condition is None and first.qubits[2]==q
            assert last.opcode==0x50 and last.condition is None and last.qubits==(q,)
            assert len(set(first.qubits))==3 and last.bit==row['measurement_bit']
            depth=0
            for op in before:
                if op.opcode==0x81:depth+=1
                elif op.opcode==0x01:depth-=1;assert depth>=0
            assert depth==0
            assert all(q not in op.qubits for op in before[1:-1])
            fresh=prof['header']['num_bits']+number
            assert all(fresh not in (op.bit,op.condition) for op in before)
            start_replacement=[P.Operation(0x50,(q,),bit=fresh),
                               P.Operation(0xa0,first.qubits[:2],condition=fresh)]
            end_replacement=[P.Operation(0x40,(),bit=last.bit),
                             P.Operation(0xc2,(),bit=last.bit,condition=fresh)]
            edits.extend([(lo,lo+1,[first],start_replacement),
                          (hi,hi+1,[last],end_replacement)])
            proofs.append(dict(start=lo,end=hi+1,target=q,controls=list(first.qubits[:2]),
                               original_bit=last.bit,fresh_bit=fresh,
                               target_references_between_endpoints=0,
                               intermediate_operations=len(before)-2,
                               intermediate_original_bit_uses=sum(op.condition==last.bit for op in before[1:-1]),
                               intermediate_original_bit_writes=sum(op.bit==last.bit for op in before[1:-1]),
                               endpoints_unconditional=True,
                               old_outcome_published_only_at_original_position=True,
                               first=op_record(first),last=op_record(last)))
            previous_end=hi
        candidate=a.out/'dqi.kmb'
        write_edits(c,candidate,edits,prof['header']['num_bits']+len(rows))
    finally:c.close()
    after=K.profile(candidate,max_register_summaries=0)
    assert prof['raw_gate_families']['CCX']['total']-after['raw_gate_families']['CCX']['total']==2
    assert after['header']['num_qubits']==prof['header']['num_qubits']==889
    assert after['header']['num_bits']==208169
    assert after['header']['num_ops']==prof['header']['num_ops']+4
    report=dict(status='EXACT_HMR_INTERVAL_REWRITE_PASS',source_sha256=SOURCE,
                candidate_sha256=after['raw_kmb_sha256'],additional_unconditional_ccx_reduction=2,
                added_conditioned_CZ=2,hmr_count_unchanged=True,qubits=889,classical_bits=208169,
                blocks=proofs,identity=identity(),native_minimal_instrument=native_identity(),
                all_intermediate_operations_unchanged=True,official_verification='NOT_RUN',
                elapsed_seconds=time.monotonic()-started)
    recipe=dict(source_sha256=SOURCE,candidate_sha256=after['raw_kmb_sha256'],
                header_num_bits=208169,
                edits=[dict(index=lo,old=op_record(old[0]),new=[op_record(x) for x in new])
                       for lo,hi,old,new in edits])
    (a.out/'rewrite_certificate.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out/'patch.json').write_text(json.dumps(recipe,indent=2)+'\n')
    (a.out/'profile.json').write_text(json.dumps(after,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
