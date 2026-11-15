#!/usr/bin/env python3
"""Splice the exact pebbled chart while preserving every old classical ID.

The emitted whole tape is an intermediate: its other kernels still require
889 wires. This script never reduces the whole header based on a local peak.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time
import dqi_ccx_peephole as Binary
import kmb_splice as S
from outcome_dqi_chart_match import match
from outcome_dqi_chart_splice_norm import encode


def classical_trace(operations):
    return [(op.opcode, op.bit, op.condition, op.angle)
            for op in operations
            if op.bit is not None or op.condition is not None or op.opcode == 1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--binding',type=Path,required=True)
    p.add_argument('--components',type=Path,required=True)
    p.add_argument('--borrow',type=int,choices=(1,6),default=6)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();started=time.monotonic()
    binding=json.loads(a.binding.read_text());components=json.loads(a.components.read_text())
    old_meta=binding['template']
    new_meta=next(row['chart_template'] for row in components['variants'] if row['borrow_bits']==a.borrow)
    c=S.open_circuit(binding['input_path']);old=S.open_circuit(old_meta['path']);new=S.open_circuit(new_meta['path'])
    assert c.profile['raw_kmb_sha256']==binding['input_sha256']
    assert old.profile['raw_kmb_sha256']==old_meta['sha256']
    assert new.profile['raw_kmb_sha256']==new_meta['sha256']
    changes={kind:[] for kind in range(1,12)};blocks=[]
    for label,oa,ob,na,nb in [('prefix',0,old_meta['prefix_ops'],0,new_meta['prefix_ops']),
        ('return',old_meta['prefix_ops'],old_meta['operations'],new_meta['prefix_ops'],new_meta['operations'])]:
        target=binding['parts'][label][0]
        original=list(old.operations(oa,ob));replacement=list(new.operations(na,nb))
        actual=list(c.operations(target['start'],target['end']))
        mapping=match(original,actual)
        assert mapping is not None
        assert classical_trace(original)==classical_trace(replacement)
        qmap={q:mapping['qubits'][q] for q in mapping['qubits'] if q<864}
        # These are caller-owned clean storage at both chart boundaries. Bank
        # 840..863 and data roles remain mapped exactly as the matched source.
        qmap.update({q:q for q in range(864,new_meta['Q'])})
        bmap=mapping['bits']
        remapped=[Binary.Operation(op.opcode,tuple(qmap[q] for q in op.qubits),
                    None if op.bit is None else bmap[op.bit],
                    None if op.condition is None else bmap[op.condition],op.angle)
                  for op in replacement]
        before_cols,after_cols=encode(actual),encode(remapped)
        for kind in range(1,11):
            lo,hi=c.column_range(kind,target['start'],target['end']);offset=c.packets[kind]['payload_offset']
            assert c.data[offset+lo:offset+hi]==before_cols[kind]
            changes[kind].append((lo,hi,after_cols[kind]))
        blocks.append(dict(label=label,start=target['start'],end=target['end'],
                           old_operations=ob-oa,new_operations=nb-na,
                           classical_trace_identical=True,new_quantum_mapping=qmap))
    sizes={kind:packet['payload_bytes'] for kind,packet in c.packets.items()}
    for kind in changes:sizes[kind]+=sum(len(buf)-(hi-lo) for lo,hi,buf in changes[kind])
    header=dict(c.profile['header'])
    for field,kind,width in [('num_ops',1,1),('num_ops_with_3_target_qubits',2,4),
        ('num_ops_with_2_target_qubits',5,4),('num_ops_with_1_target_qubits',7,4),
        ('num_ops_with_1_target_bit',8,4),('num_ops_with_1_condition_bit',9,4),('num_ops_with_angle',10,16)]:
        header[field]=sizes[kind]//width
    delta=new_meta['T']-old_meta['T']
    assert header['num_ops_with_3_target_qubits']-c.profile['header']['num_ops_with_3_target_qubits']==delta
    assert header['num_qubits']==889
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('xb') as f:
        f.write(Binary.kp.HEADER.pack(Binary.kp.MAGIC,*(header[x] for x in Binary.kp.HEADER_FIELDS)))
        Binary.copy_range(c.data,f,Binary.kp.HEADER.size,c.packets[1]['header_offset'])
        for kind in range(1,12):
            packet=c.packets[kind];base=packet['payload_offset'];cursor=0
            f.write(Binary.kp.PACKET.pack(kind,sizes[kind]))
            for lo,hi,buf in changes[kind]:
                assert lo>=cursor
                Binary.copy_range(c.data,f,base+cursor,base+lo);f.write(buf);cursor=hi
            Binary.copy_range(c.data,f,base+cursor,base+packet['payload_bytes'])
    with a.output.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    result=dict(status='EXACT_LOCAL_PEBBLE_IN_WHOLE_TAPE_GLOBAL_WIDTH_UNCHANGED',
                input_sha256=binding['input_sha256'],output_path=str(a.output),output_sha256=sha,
                header=header,static_T_delta=delta,exact_mean_T_delta=delta,
                local_chart_Q_before=old_meta['Q'],local_chart_Q_after=new_meta['Q'],
                whole_Q=889,whole_score_improvement=False,blocks=blocks,
                preservation='Original register bytes and every outside column byte copied verbatim. Same complete classical trace/IDs and HMR outcome correspondence. All temporary quantum roles at changed boundaries are clean under the same source contract.',
                scope='Intermediate only. Other consuming-product/rolling-flag kernels retain the whole 889-wire peak. No whole native or official pass claimed.',
                elapsed_seconds=time.monotonic()-started)
    a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('blocks','header')},indent=2))
    c.close();old.close();new.close()


if __name__=='__main__':main()
