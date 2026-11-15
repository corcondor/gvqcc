#!/usr/bin/env python3
"""Exact two-block patch with explicit fresh classical-mask ownership.

The original prefix/return must both match the unmodified public component.
All new temporary/deferred classical bits are allocated above the baseline
header's range; the same IDs are used in the new prefix and matching return.
"""
from pathlib import Path
import hashlib
import json
import struct
import time
import numpy as np

import dqi_ccx_peephole as Binary
import kmb_splice as S
from outcome_dqi_chart_match import match

ROOT = Path(__file__).resolve().parent


def encode(operations):
    columns = {kind: bytearray() for kind in range(1, 11)}
    for op in operations:
        columns[1].append(op.opcode)
        for kind, qubit in zip(Binary.QUANTUM_COLUMNS[len(op.qubits)], op.qubits):
            columns[kind].extend(Binary.U32.pack(qubit))
        if op.bit is not None:
            columns[8].extend(Binary.U32.pack(op.bit))
        if op.condition is not None:
            columns[9].extend(Binary.U32.pack(op.condition))
        columns[10].extend(op.angle)
    return {kind: bytes(value) for kind, value in columns.items()}


def depth(c, position):
    x = c.opcodes[:position]
    return x.count(b'\x81')-x.count(b'\x01')


def first_access_audit(c, prefix, ret, saved):
    """Prove removed scratch writes cannot feed an untouched downstream read."""
    affected = set(prefix['mapping']['bits'].values()) | set(ret['mapping']['bits'].values())
    ops = np.frombuffer(c.opcodes, dtype=np.uint8)
    accesses = []
    for column, flag, kind in [(8, 0x40, 'target'), (9, 0x80, 'condition')]:
        packet = c.packets[column]
        operands = np.frombuffer(c.data, dtype='<u4', count=packet['payload_bytes']//4,
                                 offset=packet['payload_offset'])
        operation_indices = np.flatnonzero(ops & flag)
        assert len(operation_indices) == len(operands)
        selected = np.flatnonzero(np.isin(operands, sorted(affected)))
        accesses += [(int(operation_indices[i]), int(operands[i]), kind) for i in selected]
        del operands, operation_indices, selected
    accesses.sort()
    between = [(p,b,k) for p,b,k in accesses if prefix['end'] <= p < ret['start'] and b in saved]
    assert not between, ('saved_mask_referenced_by_middle', between[:5])
    def next_access(bit, start, skip_return):
        for p,b,k in accesses:
            if b != bit or p < start or (skip_return and ret['start'] <= p < ret['end']):
                continue
            op = c.opcodes[p]
            # These unconditionally replace the target's value. An invert or
            # condition read does not establish independence from removed code.
            overwrite = k == 'target' and op in (0x40, 0x41, 0x50) and depth(c,p)==0
            return {'op': p, 'kind': k, 'opcode': hex(op), 'unconditional_overwrite': overwrite}
        return None
    rows=[]
    for label,start,ids,skip in [
        ('after_prefix',prefix['end'],set(prefix['mapping']['bits'].values()),True),
        ('after_return',ret['end'],set(ret['mapping']['bits'].values()),False)]:
        for bit in sorted(ids):
            access=next_access(bit,start,skip)
            rows.append({'boundary':label,'bit':bit,'next_untouched_access':access})
            assert access is None or access['unconditional_overwrite'], rows[-1]
    return {'saved_bits_middle_accesses':len(between), 'affected_bits':sorted(affected),
            'next_untouched_access_checks':rows}


def main():
    begun=time.monotonic()
    meta=json.loads((ROOT/'outcome_dqi_chart_norm_matches.json').read_text())
    baseline=meta['matches']['9a82']
    assert all(len(baseline['parts'][k])==1 for k in ('prefix','return'))
    prefix,ret=(baseline['parts'][k][0] for k in ('prefix','return'))
    c=S.open_circuit(baseline['path'])
    assert c.profile['raw_kmb_sha256']==baseline['sha256']
    old=S.open_circuit(meta['old_template']['file'])
    new=S.open_circuit(meta['new_template']['file'])
    saved=sum(meta['old_template']['saved_child_bits'],[])+meta['old_template']['saved_zero_bits']
    saved_global=[]
    for i in saved:
        x=prefix['mapping']['bits'][str(i)]
        assert x==ret['mapping']['bits'][str(i)]
        saved_global.append(x)
    # Quantum data and the clean owned bank must have the same physical names.
    persistent=[*range(72),*range(840,864)]
    assert all(prefix['mapping']['qubits'][str(i)]==ret['mapping']['qubits'][str(i)] for i in persistent)
    audit=first_access_audit(c,prefix,ret,set(saved_global))
    print(json.dumps({'scratch_and_mask_ownership':'PASS','saved_mask_bits':len(saved_global)}),flush=True)
    offset=c.profile['header']['num_bits']
    new_bits=meta['new_template']['bits']
    assert offset+new_bits < 2**32
    splices={kind:[] for kind in range(1,12)}
    blocks=[]
    ranges=[(prefix,0,meta['old_template']['prefix_ops'],0,meta['new_template']['prefix_ops']),
            (ret,meta['old_template']['prefix_ops'],meta['old_template']['total_ops'],
             meta['new_template']['prefix_ops'],meta['new_template']['total_ops'])]
    for target,oa,ob,na,nb in ranges:
        old_ops=list(old.operations(oa,ob))
        actual=list(c.operations(target['start'],target['end']))
        mapping=match(old_ops,actual)
        assert mapping is not None
        assert {str(k):v for k,v in mapping['qubits'].items()}==target['mapping']['qubits']
        assert {str(k):v for k,v in mapping['bits'].items()}==target['mapping']['bits']
        assert depth(c,target['start'])==depth(c,target['end'])==0
        qmap=mapping['qubits']
        replacement=[Binary.Operation(op.opcode,tuple(qmap[q] for q in op.qubits),
                        None if op.bit is None else offset+op.bit,
                        None if op.condition is None else offset+op.condition,op.angle)
                     for op in new.operations(na,nb)]
        oldcols,newcols=encode(actual),encode(replacement)
        for kind in range(1,11):
            lo,hi=c.column_range(kind,target['start'],target['end'])
            pos=c.packets[kind]['payload_offset']
            assert c.data[pos+lo:pos+hi]==oldcols[kind]
            splices[kind].append((lo,hi,newcols[kind]))
        blocks.append({'start':target['start'],'end':target['end'],'old_ops':ob-oa,
                       'new_ops':nb-na,'condition_stack_depth':0,'quantum_mapping':qmap})
    sizes={kind:packet['payload_bytes'] for kind,packet in c.packets.items()}
    for kind,changes in splices.items():
        sizes[kind]+=sum(len(buf)-(hi-lo) for lo,hi,buf in changes)
    header=dict(c.profile['header'])
    for field,kind,width in [('num_ops',1,1),('num_ops_with_3_target_qubits',2,4),
        ('num_ops_with_2_target_qubits',5,4),('num_ops_with_1_target_qubits',7,4),
        ('num_ops_with_1_target_bit',8,4),('num_ops_with_1_condition_bit',9,4),('num_ops_with_angle',10,16)]:
        header[field]=sizes[kind]//width
    header['num_bits']=offset+new_bits
    assert header['num_qubits']==889
    assert header['num_ops_with_3_target_qubits']-c.profile['header']['num_ops_with_3_target_qubits']==-14
    output=ROOT/'outcome_dqi_chart_norm_dqi_9a82_third_projective.kmb'
    with output.open('xb') as f:
        f.write(Binary.kp.HEADER.pack(Binary.kp.MAGIC,*(header[x] for x in Binary.kp.HEADER_FIELDS)))
        Binary.copy_range(c.data,f,Binary.kp.HEADER.size,c.packets[1]['header_offset'])
        for kind in range(1,12):
            packet=c.packets[kind];base=packet['payload_offset'];cursor=0
            f.write(Binary.kp.PACKET.pack(kind,sizes[kind]))
            for lo,hi,buf in splices[kind]:
                assert lo>=cursor
                Binary.copy_range(c.data,f,base+cursor,base+lo);f.write(buf);cursor=hi
            Binary.copy_range(c.data,f,base+cursor,base+packet['payload_bytes'])
    with output.open('rb') as f:
        output_hash=hashlib.file_digest(f,'sha256').hexdigest()
    result={'status':'BUILT_EXACT_TWO_BLOCK_PATCH_REQUIRES_FULL_DECODER_TEST',
        'input_sha256':baseline['sha256'],'output_path':str(output),'output_sha256':output_hash,
        'output_bytes':output.stat().st_size,'header':header,'static_T_delta':-14,
        'mean_T_delta_model':-3,'blocks':blocks,'saved_original_mask_ids':saved_global,
        'fresh_classical_bit_range':[offset,offset+new_bits],
        'new_shared_child_mask_ids':[[offset+i for i in row] for row in meta['new_template']['saved_child_bits']],
        'mask_ownership_audit':audit,
        'preservation':'All original register bytes and every operand column outside the two exact matched blocks copied verbatim. All new classical bits are fresh; the prefix and return share the same complete allocation.',
        'scope':'General D=0 repair at third public pivot, finite final output domain. N=0 and other pivots remain unextended.',
        'elapsed_seconds':time.monotonic()-begun}
    (ROOT/'outcome_dqi_chart_norm_splice_report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('mask_ownership_audit','blocks')},indent=2))
    c.close();old.close();new.close()


if __name__=='__main__':
    main()
