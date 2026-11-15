#!/usr/bin/env python3
"""Independent syntactic/coherent proof of the two-use q21 product cache.

This proof does not enumerate reachable x: the affected control wires return
identically for arbitrary other quantum data, and the cache is explicitly reset.
Only the clean-cache entry condition is used. The source's own measurements and
rotation instructions are retained byte for byte.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,re


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(lines):
    return [(line.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',line)))) for line in lines]


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=Path(__file__).with_name('invsqrt_structural_e46.kmx')
    lines=source.read_text().splitlines();ops=parse(lines);first,last,cache=3321,3423,21
    assert lines[first]==lines[last]=='CCX q10 q11 q13'
    last_ref=max(i for i in range(first) if cache in ops[i][1])
    assert ops[last_ref]==('HMR',(cache,))
    assert all(cache not in qs for _,qs in ops[last_ref+1:last+1])
    # A None entry is arbitrary nonlinear data. Conservatively taint nonlinear
    # targets while exactly tracking affine control functions.
    affine=[1<<(q+1) for q in range(46)]
    for op,qs in ops[first+1:last]:
        if op=='X':
            q,=qs
            if affine[q] is not None:affine[q]^=1
        elif op=='CX':
            q,t=qs
            affine[t]=None if affine[q] is None or affine[t] is None else affine[t]^affine[q]
        elif op=='CCX':affine[qs[2]]=None
        elif op=='SWAP':q,t=qs;affine[q],affine[t]=affine[t],affine[q]
        elif op=='CSWAP':affine[qs[1]]=affine[qs[2]]=None
        elif op=='HMR':affine[qs[0]]=0
        elif op in ('Z','CZ','CCZ','RZ','RZZ','RZZZ','RZ1','RZ2','RZ3'):pass
        else:raise AssertionError(('Unexpected interior operation',op))
    assert affine[10]==1<<11 and affine[11]==1<<12
    fresh=max(map(int,re.findall(r'\bb(\d+)\b',source.read_text())))+1
    expected=lines[:first]+['CX q13 q21',lines[first],'CX q13 q21']+lines[first+1:last]+[
        'CX q21 q13',f'HMR q21 b{fresh}',f'CZ q10 q11 if b{fresh}']+lines[last+1:]
    candidate_lines=a.candidate.read_text().splitlines();assert candidate_lines==expected
    count0=Counter(op for op,_ in ops);count1=Counter(op for op,_ in parse(candidate_lines))
    assert count0['CCX']-count1['CCX']==1
    rotations0=[line for line in lines if line.split()[0].startswith('R')]
    rotations1=[line for line in candidate_lines if line.split()[0].startswith('R')]
    assert rotations0==rotations1
    report=dict(status='PASS',source_sha256=sha(source),candidate_kmx_sha256=sha(a.candidate),
        source_lines=[first+1,last+1],cache=cache,explicit_reset_line=last_ref+1,
        clean_cache_through_first_gate=True,cache_originally_unreferenced_through_last_gate=True,
        left_control_returns_identically=True,right_control_returns_identically=True,
        unchanged_original_instructions_except_two_local_replacements=True,
        all_rotation_instructions_byte_identical=True,
        static_toffoli_before=count0['CCX']+count0['CSWAP']+count0['CCZ'],
        static_toffoli_after=count1['CCX']+count1['CSWAP']+count1['CCZ'],
        unconditional_toffoli_removed=1,additional_toffoli=0,additional_qubits=0,
        new_classical_measurement_bit=f'b{fresh}',
        new_measurement_branches=['m=0: cache reset, no phase','m=1: HMR contributes (-1)^(a*b); CZ(a,b) contributes the same sign, yielding +1'],
        coherent_identity='With cache c=0 and dirty target t, CX(t,c); CCX(a,b,t); CX(t,c) maps (t,c) to (t XOR a*b,a*b). The original interior never references c and returns controls a,b identically. Replace the final CCX(a,b,t) by CX(c,t), then HMR(c) and CZ(a,b) conditioned on its fresh result. All original wire values and measurement predicates are identical at each original instruction; the only extra phase cancels for each outcome.',
        proof_scope='Arbitrary quantum state on the other 45 wires at the first CCX, with q21 clean as established by the original preceding HMR; all original and new measurement branches. This local circuit identity implies the full valid-input contract. No optimality claim.',
        full_official_run=False,script_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
