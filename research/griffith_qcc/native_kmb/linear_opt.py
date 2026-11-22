"""Whole-native-KMB CNOT resynthesis with exact symbolic boundary proofs.

Runs over all 15 real ANGLE KMBs, keeping their original registers, HMR,
conditional CZ/Z, CCX, X and metadata. Only maximal *unconditional-CX-only*
intervals are candidates for a shorter GF(2) Gaussian synthesis. A candidate
is installed only after matrix equality is checked, not a probabilistic test.

Consequence: exact equality of the entire quantum instrument for *arbitrary*
input superpositions and all measurement transcripts, not merely legal table
addresses. This compiler makes NO PAID THREE-QUBIT SAVING: CNOT is free in
the official chemistry scoring formula. It is an integration/proof milestone,
NOT a score improvement.
"""
from __future__ import annotations
import argparse,hashlib,json,random,time,zipfile
from pathlib import Path
from .real_kmb import KMB,Op


def matrix_run(ops, wires=None):
    wires=(sorted(set(w for o in ops for w in o.wires))
           if wires is None else list(wires))
    index={w:i for i,w in enumerate(wires)}
    rows=[1<<i for i in range(len(wires))]
    for o in ops:
        if o.code!=0x21 or len(o.wires)!=2:
            raise ValueError("Only unconditional CX blocks are eligible")
        a,b=(index[q] for q in o.wires)
        if a==b:raise ValueError("Self-target CX is invalid")
        rows[b]^=rows[a]
    return wires,rows


def synthesize_rows(rows, order=None):
    """Invert an arbitrary full-rank GF(2) map by Gaussian row operations."""
    n=len(rows)
    order=list(range(n)) if order is None else list(order)
    r=[sum(((rows[order[i]]>>order[j])&1)<<j for j in range(n))
       for i in range(n)]
    reductions=[]
    def cx(a,b):
        assert a!=b
        r[b]^=r[a]
        reductions.append((a,b))
    for j in range(n):
        if not r[j]>>j&1:
            pivot=next((i for i in range(j+1,n) if r[i]>>j&1),None)
            if pivot is None:raise ValueError("Non-invertible CX block")
            cx(j,pivot);cx(pivot,j);cx(j,pivot)
        for i in range(j+1,n):
            if r[i]>>j&1:cx(j,i)
    for j in reversed(range(n)):
        for i in range(j):
            if r[i]>>j&1:cx(j,i)
    if r!=[1<<i for i in range(n)]:
        raise AssertionError("Gaussian reduction not identity")
    return [(order[a],order[b]) for a,b in reversed(reductions)]


def optimize_run(original, attempts=0):
    if len(original)<3:return list(original),False
    wires,original_map=matrix_run(original)
    n=len(wires)
    best=list(original)
    permutations=[list(range(n)),list(reversed(range(n)))]
    rng=random.Random(3041907+len(original)*37+n)
    for _ in range(attempts):
        order=list(range(n))
        rng.shuffle(order)
        permutations.append(order)
    for order in permutations:
        proposal=synthesize_rows(original_map,order)
        if len(proposal)<len(best):
            best=[Op(0x21,(wires[a],wires[b])) for a,b in proposal]
    if len(best)<len(original):
        # Symbolic equality for all binary input vectors, not sampled tests.
        assert matrix_run(best,wires)[1]==original_map
        return best,True
    return list(original),False


def partition(ops):
    """Each CNOT-only interval with its *unchanged* next non-CX gate."""
    groups=[]
    start=0
    for j,o in enumerate(ops):
        if o.code!=0x21:
            groups.append((ops[start:j],o))
            start=j+1
    groups.append((ops[start:],None))
    return groups


def certify_source_candidate(source,candidate):
    if (source.version,source.nq,source.nb,source.nregs,
        source.registers,source.tag)!=(candidate.version,candidate.nq,
        candidate.nb,candidate.nregs,candidate.registers,candidate.tag):
        raise AssertionError("KMB headers, registers or trailing metadata changed")
    left=partition(source.ops);right=partition(candidate.ops)
    if len(left)!=len(right):raise AssertionError("non-CX gate count changed")
    altered=0;src_cx=dst_cx=0
    for (a,barrier),(b,other) in zip(left,right):
        if barrier!=other:raise AssertionError("non-CX instruction modified")
        src_cx+=len(a);dst_cx+=len(b)
        if a==b:continue
        if len(b)>=len(a):raise AssertionError("replacement did not reduce CX")
        # Full 128x128 linear equality is implied by equality on the union
        # of touched physical wires plus identity on all untouched wires.
        wires=sorted({q for o in a for q in o.wires}|
                     {q for o in b for q in o.wires})
        if matrix_run(a,wires)[1]!=matrix_run(b,wires)[1]:
            raise AssertionError("GF(2) linear map differs")
        altered+=1
    if source.paid()!=candidate.paid():
        raise AssertionError("CCX count unexpectedly modified")
    return {'old_CX':src_cx,'new_CX':dst_cx,
            'saved_CX':src_cx-dst_cx,
            'changed_formally_proven_runs':altered,
            'old_CCX':source.paid(),'new_CCX':candidate.paid(),
            'phase_measurement_and_other_non_CX_instructions_identical':True}


def optimize_bank(source_path,output_path,attempts=0):
    source=KMB.read(source_path)
    if source.render()!=Path(source_path).read_bytes():
        raise AssertionError("KMB original binary did not roundtrip byte-for-byte")
    new=[]
    for cnot_run,barrier in partition(source.ops):
        replacement,_=optimize_run(cnot_run,attempts=attempts)
        new.extend(replacement)
        if barrier is not None:new.append(barrier)
    candidate=KMB(source_path,source.version,source.nq,source.nb,source.nregs,
                  source.registers,new,source.tag)
    proof=certify_source_candidate(source,candidate)
    if Path(output_path).exists():
        raise FileExistsError("Refusing to overwrite any KMB")
    candidate.write(output_path)
    readback=KMB.read(output_path)
    if readback.ops!=candidate.ops or readback.render()!=Path(output_path).read_bytes():
        raise AssertionError("KMB serialization roundtrip failed")
    proof.update(source_sha256=hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
                 output_sha256=hashlib.sha256(Path(output_path).read_bytes()).hexdigest(),
                 source_size_bytes=Path(source_path).stat().st_size,
                 output_size_bytes=Path(output_path).stat().st_size,
                 physical_qubits=source.nq)
    return proof


def optimize_all(source_dir:Path,output_dir:Path,attempts:int=0,zip_result=False):
    """Fail closed if any original bank or data member is unavailable."""
    source_dir=Path(source_dir)
    output_dir=Path(output_dir)
    source_paths=[source_dir/f"angle_k_{k}.kmb" for k in range(15)]
    if not all(p.exists() for p in source_paths):
        raise FileNotFoundError("All fifteen actual angle_k_0..14.kmb required")
    npz=source_dir/"submission.npz"
    if not npz.exists():
        raise FileNotFoundError("Original submission.npz required")
    output_dir.mkdir(parents=True,exist_ok=False)
    members=[]
    for k,p in enumerate(source_paths):
        output=output_dir/p.name
        report=optimize_bank(p,output,attempts)
        report['bank']=k
        members.append(report)
    data=npz.read_bytes()
    (output_dir/"submission.npz").write_bytes(data)
    result={
        'status':'FORMALLY_EQUIVALENT_ACTUAL_15_BANK_KMB_CX_ONLY',
        'native_official_verifier':'not_run',
        'not_a_verified_score_update':True,
        'official_paid_ccx_gain':0,
        'q_cap_128_preserved':all(v['physical_qubits']<=128 for v in members),
        'npz_sha256_unchanged':hashlib.sha256(data).hexdigest(),
        'old_CX':sum(v['old_CX'] for v in members),
        'new_CX':sum(v['new_CX'] for v in members),
        'old_CCX':sum(v['old_CCX'] for v in members),
        'new_CCX':sum(v['new_CCX'] for v in members),
        'exact_Gf2_intervals_proved':sum(v['changed_formally_proven_runs'] for v in members),
        'all_HMR_and_conditional_phase_unchanged':True,
        'members':members,
    }
    reportfile=output_dir/'formal_CX_rewrite_report.json'
    reportfile.write_text(json.dumps(result,indent=2)+'\n')
    if zip_result:
        archive=output_dir.parent/(output_dir.name+"_RESEARCH_ONLY.zip")
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for k in range(15):z.write(output_dir/f'angle_k_{k}.kmb',f'dfthcsos/angle_k_{k}.kmb')
            z.write(output_dir/'submission.npz','dfthcsos/submission.npz')
            z.write(reportfile,'formal_CX_rewrite_report.json')
        result['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-angles',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--attempts',type=int,default=0)
    p.add_argument('--zip',action='store_true')
    args=p.parse_args()
    if args.attempts<0 or args.attempts>64:raise ValueError('attempts outside 0..64')
    result=optimize_all(args.original_angles,args.output,args.attempts,args.zip)
    print(json.dumps({k:v for k,v in result.items() if k!='members'},indent=2))


if __name__=='__main__':
    main()
