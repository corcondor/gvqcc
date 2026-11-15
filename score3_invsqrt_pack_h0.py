#!/usr/bin/env python3
"""Concrete e46 h0 packing/rematerialization at the first width peak.

This is a local width reduction, not a claim of whole-circuit Q45. Full-domain
truth identities certify the new measurement phase and restoration. The source
generator's optional h0 packing is adapted to the actual e46 physical wires.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

import score_invsqrt_retire as model


PACK_CUT, RESTORE_CUT = 1635, 3428  # Number of original lines already executed.
SOURCE = Path(__file__).with_name('invsqrt_structural_e46.kmx')
PIN = '69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1'


def advance_lines(lines, values, domain):
    for line in lines:
        model.advance(line.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',line))),values,domain)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    began=time.monotonic()
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
    lines,ops=model.instructions(SOURCE)
    assert lines[PACK_CUT]=='X q36' and lines[RESTORE_CUT]=='CX q0 q45'
    fresh_bit=max(map(int,re.findall(r'\bb(\d+)\b',raw.decode())))+1
    pack=['X q0','CX q12 q0','CX q13 q0','CX q14 q0','CX q36 q0',
          'CX q0 q24','CX q0 q25',f'HMR q0 b{fresh_bit}',f'CZ q24 q25 if b{fresh_bit}']
    domain,values=model.initial_values();stack=[]
    for op,qubits in ops[:PACK_CUT]:
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':
            before=stack.pop();assert before==values;values=before
        else:model.advance(op,qubits,values,domain)
    assert not stack
    before_pack=values[:]
    packed=values[:]
    advance_lines(pack[:7],packed,domain)
    phase_identity=(packed[0] == (packed[24]&packed[25]))
    if not phase_identity:
        difference=packed[0]^(packed[24]&packed[25]);witness=(difference&-difference).bit_length()-1
        result=dict(status='REJECTED_PACK_IDENTITY',witness_input=witness,source_sha256=PIN)
        (args.out/'proof.json').write_text(json.dumps(result,indent=2)+'\n')
        raise AssertionError(result)
    packed[0]=0
    original_peak_positions=[]
    packed_peak_positions=[]
    for i,(op,qubits) in enumerate(ops[PACK_CUT:RESTORE_CUT],PACK_CUT):
        if set(qubits)&{0,24,25}:raise AssertionError(('Packed owner read during interval',i+1,lines[i]))
        if op=='PUSH_CONDITION':stack.append((values[:],packed[:]))
        elif op=='POP_CONDITION':
            old,new=stack.pop();assert old==values and new==packed
            values,packed=old,new
        else:
            model.advance(op,qubits,values,domain)
            model.advance(op,qubits,packed,domain)
        if all(values):original_peak_positions.append(i+1)
        if all(packed):packed_peak_positions.append(i+1)
    assert not stack and not packed[0]
    restore2=['CCX q24 q25 q0','CX q0 q24','CX q0 q25',
              'CX q10 q0','CX q12 q0','CX q13 q0','CX q14 q0',
              'CX q10 q13','X q13','CCX q39 q13 q0','X q13','CX q10 q13']
    test=packed[:];advance_lines(restore2,test,domain)
    used=2
    if test!=values:
        # Source fallback: exact three-AND expression independent of seed5.
        helper=next(q for q in (44,21,34,36) if not packed[q])
        restore3=['CCX q24 q25 q0','CX q0 q24','CX q0 q25',
                  'CX q10 q11','CX q10 q12',f'CCX q11 q12 q{helper}',
                  'CX q10 q12','CX q10 q11',
                  'X q0','CX q12 q0','CX q14 q0',
                  'CX q10 q13','X q13',f'CCX q{helper} q13 q0','X q13','CX q10 q13',
                  f'HMR q{helper} b{fresh_bit+1}','CX q10 q11','CX q10 q12',
                  f'CZ q11 q12 if b{fresh_bit+1}','CX q10 q12','CX q10 q11']
        test=packed[:];advance_lines(restore3,test,domain)
        restore=restore3;used=3
    else:restore=restore2
    if test!=values:
        differences=[a^b for a,b in zip(test,values)];combined=0
        for v in differences:combined|=v
        result=dict(status='REJECTED_RECONSTRUCTION',witness_input=(combined&-combined).bit_length()-1,
                    differing_qubits=[q for q,v in enumerate(differences) if v],source_sha256=PIN)
        (args.out/'proof.json').write_text(json.dumps(result,indent=2)+'\n')
        raise AssertionError(result)
    output=lines[:PACK_CUT]+pack+lines[PACK_CUT:RESTORE_CUT]+restore+lines[RESTORE_CUT:]
    kmx=args.out/'candidate.kmx';kmx.write_text('\n'.join(output)+'\n')
    import kickmix as km
    source_circuit=km.Circuit(raw.decode());candidate=km.Circuit('\n'.join(output)+'\n')
    kmb=args.out/'candidate.kmb';candidate.to_file(kmb,format='kmb')
    original_peaks=json.loads(SOURCE.with_name('score_invsqrt_retire.json').read_text())['positions_with_all46_nonzero']
    record=dict(status='EXACT_LOCAL_PACK_AND_RECONSTRUCTION_PASS',valid_inputs=model.MAX_X,
                source_sha256=PIN,kmx_sha256=hashlib.sha256(kmx.read_bytes()).hexdigest(),
                kmb_sha256=hashlib.sha256(kmb.read_bytes()).hexdigest(),
                pack_before_original_line=PACK_CUT+1,restore_before_original_line=RESTORE_CUT+1,
                owner='q0=h0; q24/q25=packed exponent flags; q36=root conversion carry',
                new_measurement_phase_identity='packed_h0 == packed_flag2 AND packed_flag3 on every legal input',
                all_new_HMR_branches_phase_correct=True,restored_all46_values=True,
                additional_unconditional_ccx=used,
                source_static_toffoli=int(source_circuit.operation_statistics().num_toffoli_like),
                candidate_static_toffoli=int(candidate.operation_statistics().num_toffoli_like),
                source_qubits=source_circuit.num_qubits,candidate_qubits=candidate.num_qubits,
                freed_original_peak_positions=len(original_peak_positions),
                still_full_local_peak_positions=len(packed_peak_positions),
                original_whole_tape_full_peak_positions=len(original_peaks),
                remaining_original_full_peak_positions=len(set(original_peaks)-set(original_peak_positions)),
                whole_Q45=False,score_improvement_claimed=False,
                original_circuit_unchanged_between_and_outside_patches=True,
                exact_scope='New patch maps equal source at both cuts; no source gate reads packed owners between cuts. Full valid-input identities plus exact phase correction imply equality of all original downstream phases and restoration.',
                pack_lines=pack,restore_lines=restore,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                seconds=time.monotonic()-began)
    assert record['candidate_static_toffoli']-record['source_static_toffoli']==used
    assert not packed_peak_positions
    (args.out/'proof.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)


if __name__=='__main__':main()
