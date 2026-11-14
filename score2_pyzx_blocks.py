#!/usr/bin/env python3
"""Run actual PyZX graph reduction/extraction on large measured-free blocks.

Only an exact affine output with fewer operations may be written back. The
independent GF(2) map check is mandatory even when PyZX verifies equality.
Global phases and wire permutations are included in the PyZX equality check.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import pyzx as zx
import kickmix as km
from score2_clifford_affine_reduce import parse,affine


def blocks(lines):
    output=[];start=None
    for i,line in enumerate(lines+['END']):
        if parse(line) is not None:
            if start is None:start=i
        elif start is not None:
            if i-start>=10:output.append((start,i))
            start=None
    return output


def from_zx(circuit,wires):
    out=[]
    for g in circuit.gates:
        if g.name=='CNOT':out.append(('CX',(wires[g.control],wires[g.target])))
        elif g.name=='NOT':out.append(('X',(wires[g.target],)))
        elif g.name=='SWAP':out.append(('SWAP',(wires[g.control],wires[g.target])))
        elif g.name in ('ZPhase','XPhase') and g.phase%2==0:pass
        else:return None
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--blocks',type=int,default=12)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    args.out.mkdir(parents=True);start=time.monotonic()
    circuits={};all_blocks=[];pins={}
    for path in sorted(args.loaders.glob('angle_k_*.kmb')):
        circuits[path.name]=str(km.Circuit.from_file(path)).splitlines()
        pins[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for lo,hi in blocks(circuits[path.name]):all_blocks.append((hi-lo,path.name,lo,hi))
    all_blocks.sort(reverse=True)
    rows=[];replacements={};report={'pyzx_version':zx.__version__,'status':'RUNNING','source_hashes':pins,
                                 'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                 'source_directory':str(args.loaders),'blocks':rows,'nonclifford_cost_change':0}
    for _,name,lo,hi in all_blocks[:args.blocks]:
        t=time.monotonic();ops=[parse(x) for x in circuits[name][lo:hi]]
        wires=sorted({q for _,qs in ops for q in qs});index={q:i for i,q in enumerate(wires)}
        c=zx.Circuit(len(wires))
        for gate,qs in ops:
            c.add_gate({'CX':'CNOT','X':'NOT','SWAP':'SWAP'}[gate],*(index[q] for q in qs))
        g=c.to_graph();vertices_before=g.num_vertices()
        zx.simplify.full_reduce(g)
        vertices_after=g.num_vertices()
        extracted=zx.extract_circuit(g,up_to_perm=False,optimize_cnots=3,quiet=True)
        optimized=zx.optimize.basic_optimization(extracted.to_basic_gates(),do_swaps=False,quiet=True)
        equivalent=c.verify_equality(optimized,up_to_swaps=False,up_to_global_phase=False)
        if not equivalent:raise AssertionError('PyZX equality verification failed')
        candidate=from_zx(optimized,wires)
        row={'file':name,'start_zero_based':lo,'end_exclusive':hi,'qubits':len(wires),
             'source_gates':len(ops),'zx_extracted_gates':len(optimized.gates),
             'vertices_before':vertices_before,'vertices_after':vertices_after,
             'zx_exact_equality':equivalent,'affine_gate_set_restored':candidate is not None,
             'extracted_gate_types':sorted({x.name for x in optimized.gates})}
        if candidate is not None:
            row['independent_affine_equal']=affine(candidate,wires)==affine(ops,wires)
            if not row['independent_affine_equal']:raise AssertionError('Independent affine mismatch')
            row['accepted']=len(candidate)<len(ops)
            if row['accepted']:
                replacements.setdefault(name,{})[lo]=(hi,[' '.join([gate]+[f'q{q}' for q in qs]) for gate,qs in candidate])
                row['removed_gates']=len(ops)-len(candidate)
        else:row['accepted']=False
        row['seconds']=time.monotonic()-t;rows.append(row)
        (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(row),flush=True)
    for name,original in circuits.items():
        out=[];i=0
        while i<len(original):
            if i in replacements.get(name,{}):
                i,new=replacements[name][i];out.extend(new)
            else:out.append(original[i]);i+=1
        dest=args.out/name
        if name in replacements:km.Circuit('\n'.join(out)+'\n').to_file(dest,format='kmb')
        else:dest.write_bytes((args.loaders/name).read_bytes())
    report['status']='COMPLETE'
    report['removed_gates']=sum(x.get('removed_gates',0) for x in rows)
    report['seconds']=time.monotonic()-start
    report['candidate_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.glob('angle_k_*.kmb')}
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'COMPLETE','removed_gates':report['removed_gates'],'seconds':report['seconds']}),flush=True)


if __name__=='__main__':main()
