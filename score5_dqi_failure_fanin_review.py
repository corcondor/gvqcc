#!/usr/bin/env python3
"""Independent exact proof and whole-binary binding of the eight fan-in edits.

Uses shared binary readers, but neither the discovery scanner nor the patcher's
commutation predicate, rewrite implementation, or native checker. The complete
candidate is read-only and memory-mapped. No official verification is run.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import time

import kmb_profile as K
from dqi_ccx_peephole import BinaryCircuit, Operation
from kmb_splice import compare_ranges, register_bytes

OLD_SHA='98ad7b39a630a4152c54b39fbb14dece22fcaf34b00410ab8a45629db87e0b6f'
NEW_SHA='6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def signature(op):
    return [op.opcode,list(op.qubits),op.bit,op.condition,op.angle.hex()]


def recorded_signature(row):
    return [row['opcode'],row['qubits'],row['bit'],row['condition'],row['angle_hex']]


def digest_ops(ops):
    raw=json.dumps([signature(o) for o in ops],separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest()


def independently_commutes(ccx,other):
    """Only the four instrument types actually present in these eight spans.

    The moved unconditioned CCX leaves all classical bits untouched. It may
    share controls with diagonal gates; its target cannot occur in their
    support. HMR must be disjoint from every CCX operand, ensuring exact
    commutation separately for each measurement outcome and phase kickback.
    """
    a,b,t=ccx.qubits
    base=other.opcode & 127
    if base in (0x21,0x31):
        return other.qubits[-1] not in (a,b) and t not in other.qubits[:-1]
    if base==0x20:
        return t not in other.qubits
    if base==0x50:
        return not set((a,b,t)) & set(other.qubits)
    return False


def check_header_and_packets(c):
    header=K.HEADER.unpack_from(c.data,0)
    assert header[0]==K.MAGIC
    assert dict(zip(K.HEADER_FIELDS,header[1:]))==c.profile['header']
    for kind,row in c.packets.items():
        assert K.PACKET.unpack_from(c.data,row['header_offset'])==(kind,row['payload_bytes'])
    end=c.packets[11]['payload_offset']+c.packets[11]['payload_bytes']
    assert end==len(c.data)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=Path('/workspace/scratch/3815fb5fae06/score5_norm_fanout/dqi.kmb'))
    ap.add_argument('--build',type=Path,default=Path('/workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin'))
    ap.add_argument('--output',type=Path,default=Path(__file__).with_suffix('.json'))
    args=ap.parse_args();begun=time.monotonic()
    cert_path=args.build/'rewrite_certificate.json'
    certificate=json.loads(cert_path.read_text())
    old_profile=json.loads((args.source.parent/'after_profile.json').read_text())
    new_profile=json.loads((args.build/'profile.json').read_text())
    candidate=args.build/'dqi.kmb'
    assert sha(args.source)==old_profile['raw_kmb_sha256']==certificate['source_sha256']==OLD_SHA
    assert sha(candidate)==new_profile['raw_kmb_sha256']==certificate['candidate_sha256']==NEW_SHA
    for a,b,c,t in itertools.product((0,1),repeat=4):
        old=(a,b,c,t^(a&b)^(a&c))
        temp=c^b
        new=(a,b,temp^b,t^(a&temp))
        assert old==new
    old=BinaryCircuit(args.source,old_profile)
    new=BinaryCircuit(candidate,new_profile)
    groups=[];gaps=[];families=Counter();old_cursor=new_cursor=offset=0
    try:
        check_header_and_packets(old);check_header_and_packets(new)
        assert register_bytes(old)==register_bytes(new)
        increments={'num_ops':8,'num_ops_with_3_target_qubits':-8,
                    'num_ops_with_2_target_qubits':16}
        for k,v in old_profile['header'].items():
            assert new_profile['header'][k]==v+increments.get(k,0),(k,v,new_profile['header'][k])
        assert new_profile['header']['num_qubits']==889 and new_profile['header']['num_bits']==208167
        assert old_profile['header']['num_info_tags']==new_profile['header']['num_info_tags']==0
        for c in (old,new):
            p=c.packets[11]
            assert c.data[p['payload_offset']:p['payload_offset']+p['payload_bytes']]==b'\0'*8
        assert len(certificate['blocks'])==8
        for block in certificate['blocks']:
            lo,hi=block['start'],block['end']
            assert old_cursor<=lo<hi and len(block['steps'])==1
            assert block['native']=={'basis_inputs':256,'quantum_errors':0,'classical_errors':0,'phase_errors':0}
            assert old.opcodes[:lo].count(0x81)==old.opcodes[:lo].count(0x01)
            original=list(old.operations(lo,hi))
            assert [signature(o) for o in original]==[recorded_signature(o) for o in block['before']]
            assert [o.source_index for o in original]==[o['source_index'] for o in block['before']]
            first,last=original[0],original[-1]
            step=block['steps'][0]
            assert first.source_index==step['first'] and last.source_index==step['second']
            assert first.opcode==last.opcode==0x31
            assert first.condition is last.condition is None
            t=first.qubits[2]
            assert last.qubits[2]==t
            common=set(first.qubits[:2]) & set(last.qubits[:2])
            assert len(common)==1
            a=common.pop();b=(set(first.qubits[:2])-{a}).pop();c=(set(last.qubits[:2])-{a}).pop()
            assert len({a,b,c,t})==4
            assert (a,[b,c],t)==(step['common_control'],step['other_controls'],step['target'])
            middle=original[1:-1]
            assert all(o.opcode not in (0x01,0x81) for o in original)
            assert all(independently_commutes(first,o) for o in middle)
            families.update(K.OPCODES[o.opcode] for o in middle)
            independently_rewritten=middle+[Operation(0x21,(b,c)),Operation(0x31,(a,c,t)),Operation(0x21,(b,c))]
            assert [signature(o) for o in independently_rewritten]==[recorded_signature(o) for o in block['after']]
            new_lo,new_hi=lo+offset,hi+offset+1
            check=compare_ranges(old,old_cursor,lo,new,new_cursor,new_lo)
            assert check['equal']
            gaps.append({'source':[old_cursor,lo],'candidate':[new_cursor,new_lo],
                         'all_ten_operation_columns_byte_equal':True})
            actual=list(new.operations(new_lo,new_hi))
            assert [signature(o) for o in actual]==[signature(o) for o in independently_rewritten]
            groups.append({'source':[lo,hi],'candidate':[new_lo,new_hi],
                           'independent_before_sha256':digest_ops(original),
                           'independent_after_sha256':digest_ops(independently_rewritten),
                           'actual_candidate_matches':True,'all_crossed_instruments_commute':True})
            old_cursor=hi;new_cursor=new_hi;offset+=1
        assert offset==8
        check=compare_ranges(old,old_cursor,len(old.opcodes),new,new_cursor,len(new.opcodes))
        assert check['equal']
        gaps.append({'source':[old_cursor,len(old.opcodes)],'candidate':[new_cursor,len(new.opcodes)],
                     'all_ten_operation_columns_byte_equal':True})
        assert old.opcodes.count(0x31)-new.opcodes.count(0x31)==8
        assert new.opcodes.count(0x21)-old.opcodes.count(0x21)==16
    finally:
        old.close();new.close()
    result={'status':'INDEPENDENT_FANIN_INSTRUMENT_AND_FULL_BINARY_BINDING_PASS',
        'source_sha256':OLD_SHA,'candidate_sha256':NEW_SHA,
        'exact_unconditional_ccx_reduction':8,'exact_added_cx':16,
        'quantum_width':889,'classical_bits':208167,
        'identity_basis_columns_checked':16,
        'phase_proof':'Exact equal permutation matrices with positive basis amplitudes; '
                      'commutation holds for each independent HMR outcome and its classical feedback.',
        'crossed_operations':dict(families),'groups':groups,'unchanged_ranges':gaps,
        'register_bytes_identical':True,'header_changes_only_expected_counts':True,
        'all_other_operation_columns_byte_identical':True,
        'source_and_candidate_opened_read_only':True,
        'root_native_receipts_reviewed':{'blocks':8,'inputs_per_block':256,
                                         'all_reported_value_classical_phase_errors_zero':True},
        'new_native_or_official_run_performed':False,
        'root_certificate_sha256':sha(cert_path),'root_patch_sha256':sha(args.build/'patch.json'),
        'audit_script_sha256':sha(__file__),'elapsed_seconds':time.monotonic()-begun,
        'scope':'Eight new fan-in identities are exactly bound to candidate6a998c. '
                'This preserves every predecessor instrument including the prior chart repair '
                'and sixteen fan-out edits. Full official cost/error measurement is separate. '
                'No claim of fixing the remaining numerator-zero class or a new Public Score.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'receipt_sha256':sha(args.output),
                      'candidate_sha256':NEW_SHA,'crossed_operations':result['crossed_operations'],
                      'elapsed_seconds':result['elapsed_seconds']},indent=2))


if __name__=='__main__':main()
