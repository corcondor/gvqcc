#!/usr/bin/env python3
"""Bind the independent local proof to the immutable complete DQI candidate."""
import argparse,hashlib,json
from pathlib import Path
from dqi_ccx_peephole import BinaryCircuit
from kmb_splice import compare_ranges,register_bytes
from score4_dqi_guard_review import text

def sha(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    root=Path(__file__).parent
    review_path=root/'score4_dqi_guard_review.json';review=json.loads(review_path.read_text())
    certificate_path=args.build/'rewrite_certificate.json';certificate=json.loads(certificate_path.read_text())
    old_path=Path(certificate['source']);new_path=args.build/'dqi.kmb'
    old_profile=json.loads((args.build/'before_profile.json').read_text());new_profile=json.loads((args.build/'after_profile.json').read_text())
    assert sha(old_path)==old_profile['raw_kmb_sha256']==review['source_sha256']==certificate['source_sha256']
    new_sha=sha(new_path)
    assert new_sha==new_profile['raw_kmb_sha256']==certificate['candidate_sha256']=='5a60d66233198be8ce05d9710bd35a7d2d6700bbced87560d405651070ae8194'
    old=BinaryCircuit(old_path,old_profile);new=BinaryCircuit(new_path,new_profile)
    assert register_bytes(old)==register_bytes(new)
    allowed={'num_ops':16,'num_ops_with_3_target_qubits':-16,'num_ops_with_2_target_qubits':32}
    for key,value in old_profile['header'].items():assert new_profile['header'][key]==value+allowed.get(key,0),(key,value,new_profile['header'][key])
    assert old_profile['header']['num_info_tags']==new_profile['header']['num_info_tags']==0
    groups=[];gaps=[];old_cursor=new_cursor=offset=0
    for group in review['groups']:
        lo,hi=group['start'],group['end'];new_lo=lo+offset
        new_hi=hi+offset+len(group['pairs'])
        unchanged=compare_ranges(old,old_cursor,lo,new,new_cursor,new_lo)
        assert unchanged['equal']
        gaps.append(dict(source_start=old_cursor,source_end=lo,candidate_start=new_cursor,candidate_end=new_lo,
                         operation_count=lo-old_cursor,all_ten_operand_columns_equal=True))
        before=text(list(old.operations(lo,hi)));after=text(list(new.operations(new_lo,new_hi)))
        assert hashlib.sha256(before.encode()).hexdigest()==group['original_local_sha256']
        assert hashlib.sha256(after.encode()).hexdigest()==group['rewritten_local_sha256']
        groups.append(dict(source_start=lo,source_end=hi,candidate_start=new_lo,candidate_end=new_hi,
                           independently_proved_after_text_sha256=group['rewritten_local_sha256'],actual_candidate_matches=True))
        old_cursor=hi;new_cursor=new_hi;offset+=len(group['pairs'])
    unchanged=compare_ranges(old,old_cursor,len(old.opcodes),new,new_cursor,len(new.opcodes));assert unchanged['equal']
    gaps.append(dict(source_start=old_cursor,source_end=len(old.opcodes),candidate_start=new_cursor,candidate_end=len(new.opcodes),
                     operation_count=len(old.opcodes)-old_cursor,all_ten_operand_columns_equal=True))
    assert offset==16 and len(groups)==8
    old.close();new.close()
    result=dict(status='INDEPENDENT_FULL_BINARY_PROOF_BINDING_PASS',source_sha256=review['source_sha256'],candidate_sha256=new_sha,
                local_review_sha256=sha(review_path),review_script_sha256=sha(root/'score4_dqi_guard_review.py'),binding_script_sha256=sha(__file__),
                root_certificate_sha256=sha(certificate_path),root_patch_sha256=sha(args.build/'patch.json'),
                registers_byte_identical=True,headers_changed_only_expected_gate_counts=True,
                info_tags_absent=True,all_replacement_blocks_match_independent_proof=True,
                all_other_operation_columns_byte_identical=True,quantum_width=889,classical_bits=208087,
                exact_unconditional_toffoli_reduction=16,exact_added_cx=32,groups=groups,unchanged_ranges=gaps,
                scope='Full binary binding to the independently proved instrument identities. No new native or official verification was run here.',
                official_verification='Separate root receipt',public_score_claimed=False)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],candidate_sha256=new_sha,output_sha256=sha(args.output))))

if __name__=='__main__':main()
