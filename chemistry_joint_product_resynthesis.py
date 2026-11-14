#!/usr/bin/env python3
"""Bounded simultaneous-product resynthesis of ANGLE XOR accumulation blocks.

Extracts both CCX controls in one entry linear frame and each target direction
in one exit frame. Searches two-factor merges, shared-factor flip/merge moves,
and exact GF(2) quadratic-form rank decompositions at identical output direction.
No conjectured input constraints are used by these algebraic identities.
Every emitted family is separately proved on both actual batch directions.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import resource
import shutil
import time

import kickmix as km
import numpy as np

from chemistry_affine_span_resynthesis import basis_expression, parse_line
from chemistry_reachable_exact_proof import pack, prove_one

TAGS = {18,26,34,42,50}
DATA = [q for q in range(11,51) if q not in TAGS]
DATA_INDEX = {q:i for i,q in enumerate(DATA)}


def canonical(term):
    a,b,w = term
    return (min(a,b),max(a,b),w)


def classify(term):
    a,b,w = canonical(term)
    if not a or not b or not w or a ^ b == 1:
        return "zero", None
    if a == b:
        return "linear", (a,w)
    if a == 1:
        return "linear", (b,w)
    return "quadratic", (a,b,w)


def keys(term):
    a,b,w = term
    return [(0,a,b),(1,a,w),(1,b,w)]


def merge_pair(left,right):
    a,b,w = left; c,d,v = right
    if (a,b) == (c,d): return canonical((a,b,w^v))
    if w == v:
        for shared,x in [(a,b),(b,a)]:
            if shared == c: return canonical((shared,x^d,w))
            if shared == d: return canonical((shared,x^c,w))
    raise ValueError("No two shared factors")


def reduce_terms(terms, linears):
    terms = list(terms); linears = list(linears)
    while True:
        changed = False; output=[]; index={}
        for term in terms:
            kind, item = classify(term)
            if kind == "zero": changed=True; continue
            if kind == "linear": linears.append(item); changed=True; continue
            match = next((index[key] for key in keys(item) if key in index),None)
            if match is not None:
                old=output[match]
                for key in keys(old): index.pop(key,None)
                output[match]=None
                output.append(merge_pair(old,item))
                changed=True
            else:
                index.update({key:len(output) for key in keys(item)})
                output.append(item)
        terms=[x for x in output if x is not None]
        if not changed: return terms,linears


def flip_options(t1,t2):
    a,b,w=t1; c,d,v=t2
    # A common control is the shared tensor factor; its two partners are
    # respectively the other control and the output direction.
    for common,x in [(a,b),(b,a)]:
        for same,y in [(c,d),(d,c)]:
            if common == same:
                yield (canonical((common,x^y,w)),canonical((common,y,w^v)))
                yield (canonical((common,x,w^v)),canonical((common,x^y,v)))
    # With common output, both orientations of each commutative product matter.
    if w == v:
        for x,y in [(a,b),(b,a)]:
            for z,t in [(c,d),(d,c)]:
                yield (canonical((x^z,y,w)),canonical((z,y^t,w)))
                yield (canonical((x,y^t,w)),canonical((x^z,t,w)))


def try_one_flip(terms,linears,deadline):
    index=defaultdict(set)
    for i,term in enumerate(terms):
        for key in keys(term): index[key].add(i)
    checked=0
    for i,j in itertools.combinations(range(len(terms)),2):
        if time.monotonic() > deadline:
            return terms,linears,checked,False,True
        for proposed in flip_options(terms[i],terms[j]):
            checked+=1
            can_reduce=False
            for term in proposed:
                kind,item=classify(term)
                if kind != "quadratic": can_reduce=True; break
                if any(index[key]-{i,j} for key in keys(item)):
                    can_reduce=True;break
            if not can_reduce: continue
            trial=[term for n,term in enumerate(terms) if n not in {i,j}]+list(proposed)
            reduced, new_linear=reduce_terms(trial,linears)
            if len(reduced)<len(terms):
                return reduced,new_linear,checked,True,False
    return terms,linears,checked,False,False


def product_anf(a,b):
    # Bit 0 of a control vector is the affine constant. Other bit positions
    # identify Boolean entry-frame variables. x_i*x_i = x_i is retained.
    result=set()
    ia=[i for i in range(a.bit_length()) if a>>i&1]
    ib=[i for i in range(b.bit_length()) if b>>i&1]
    for i in ia:
        for j in ib:
            monomial=(0 if i==0 else 1<<i)|(0 if j==0 else 1<<j)
            if monomial in result: result.remove(monomial)
            else: result.add(monomial)
    return result


def quadratic_rank_decomposition(terms,linears):
    groups=defaultdict(list)
    for term in terms: groups[term[2]].append(term)
    result=[]; linears=list(linears); statistics=[]
    for w,group in groups.items():
        if len(group)<2:
            result.extend(group);continue
        polynomial=set()
        for a,b,_ in group: polynomial.symmetric_difference_update(product_anf(a,b))
        products=[]
        while True:
            edges=[m for m in polynomial if m.bit_count()==2]
            if not edges: break
            edge=min(edges)
            i=edge & -edge; j=edge^i
            a=i; b=j
            for m in edges:
                if m==edge: continue
                if m&i: b^=m^i
                if m&j: a^=m^j
            products.append(canonical((a,b,w)))
            polynomial.symmetric_difference_update(product_anf(a,b))
        assert all(m.bit_count()<=1 for m in polynomial)
        remainder=0
        for monomial in polynomial:
            remainder ^= monomial or 1
        statistics.append({"original_products":len(group),"rank_products":len(products)})
        if len(products)<len(group):
            result.extend(products)
            if remainder: linears.append((remainder,w))
        else:
            result.extend(group)
    return result,linears,statistics


def extract(circuit):
    lines=str(circuit).splitlines()
    parsed=[parse_line(line) for line in lines]
    core=[i for i,(g,qs,c) in enumerate(parsed) if g=="CCX" and qs[-1] in DATA_INDEX]
    if not core: raise ValueError("No output accumulation CCX")
    first,last=core[0],core[-1]+1
    pool=[q for q in range(circuit.num_qubits) if q not in DATA_INDEX]
    frame=[(1<<(q+1)) if q in pool else 0 for q in range(circuit.num_qubits)]
    terms=[]; positions=[]; linear=[]
    direction={q:1<<DATA_INDEX[q] for q in DATA}
    directions={}
    for i in reversed(range(first,last)):
        gate,qs,cond=parsed[i]
        if gate=="CX" and qs[0] in DATA_INDEX and qs[1] in DATA_INDEX:
            direction[qs[0]] ^= direction[qs[1]]
        elif gate=="CCX":
            if qs[-1] not in DATA_INDEX: raise ValueError("Nonlinear control update inside block")
            directions[i]=direction[qs[-1]]
    for i in range(first,last):
        gate,qs,cond=parsed[i]
        if cond is not None: raise ValueError("Conditioned operation inside block")
        if gate=="CCX":
            a,b,t=qs
            if t not in DATA_INDEX or a not in pool or b not in pool:
                raise ValueError("Nonlinear output read by a subsequent nonlinear gate")
            terms.append(canonical((frame[a],frame[b],directions[i])))
            positions.append(i)
        elif gate=="CX":
            a,b=qs
            if b in pool:
                if a not in pool: raise ValueError("Output-to-control dependency")
                frame[b]^=frame[a]
            linear.append(lines[i])
        elif gate=="X":
            if qs[0] in pool: frame[qs[0]]^=1
            linear.append(lines[i])
        else:
            raise ValueError("Nonlinear/measurement boundary inside block: "+gate)
    return {"lines":lines,"first":first,"last":last,"terms":terms,"linear":linear,"exit_frame":frame,"pool":pool,"positions":positions}


def synthesize(extraction,terms,linears):
    frame=list(extraction["exit_frame"])
    n=len(frame); code=[]
    def expression(value):
        result=basis_expression(frame,value,-1,1)
        if result is None: raise ValueError("Control not in exit linear span")
        wires=[q for q in range(n) if result>>q&1]
        constant=bool(result>>n&1)
        return wires,constant
    def prepare(value, excluded=None):
        wires,constant=expression(value)
        pivots=[q for q in wires if q!=excluded]
        if not pivots: raise ValueError("Independent CCX control unavailable")
        target=pivots[0]; actions=[]
        for q in wires:
            if q!=target:
                actions.append(f"CX q{q} q{target}")
                frame[target]^=frame[q]
        if constant:
            actions.append(f"X q{target}");frame[target]^=1
        assert frame[target]==value
        code.extend(actions)
        return target,actions
    def undo(actions):
        for line in reversed(actions):
            gate,qs,_=parse_line(line)
            if gate=="CX":frame[qs[1]]^=frame[qs[0]]
            else:frame[qs[0]]^=1
            code.append(line)
    for value,w in linears:
        wires,constant=expression(value)
        for q in DATA:
            if w>>DATA_INDEX[q]&1:
                if constant:code.append(f"X q{q}")
                code.extend(f"CX q{c} q{q}" for c in wires)
    for a,b,w in terms:
        pa,ops_a=prepare(a)
        pb,ops_b=prepare(b,pa)
        targets=[q for q in DATA if w>>DATA_INDEX[q]&1]
        t=targets[0]
        fanout=[f"CX q{t} q{q}" for q in targets[1:]]
        code.extend(fanout)
        code.append(f"CCX q{pa} q{pb} q{t}")
        code.extend(reversed(fanout))
        undo(ops_b);undo(ops_a)
    assert frame==extraction["exit_frame"]
    lines=extraction["lines"]
    return "\n".join(lines[:extraction["first"]]+extraction["linear"]+code+lines[extraction["last"]:])+"\n"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders",required=True,type=Path)
    parser.add_argument("--table",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    parser.add_argument("--report",required=True,type=Path)
    parser.add_argument("--seconds",type=float,default=480)
    args=parser.parse_args()
    if args.report.exists() or args.output_dir.exists():raise FileExistsError("Use fresh outputs")
    started=time.monotonic();deadline=started+args.seconds
    with np.load(args.table,allow_pickle=False) as data:words=data["angle_words"].astype(np.uint64)
    assert words.shape==(1220,75)
    address=np.arange(len(words),dtype=np.uint64)
    address_bits=[pack((address>>q)&1) for q in range(11)]
    zero=np.zeros((len(words),5),dtype=np.uint64)
    rows=[]; candidates=[]
    for k in range(15):
        path=args.loaders/f"angle_k_{k}.kmb";source=km.Circuit.from_file(path)
        row={"k":k,"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"source_ccx":int(source.operation_statistics().num_toffoli_like)}
        try:ex=extract(source)
        except ValueError as exc:
            row.update(status="OUTSIDE_EXTRACTABLE_CLASS",reason=str(exc),ccx_removed=0)
            rows.append(row);candidates.append(source);print(json.dumps(row),flush=True);continue
        terms,linears=reduce_terms(ex["terms"],[])
        row.update(core_products=len(ex["terms"]),direct_merge_reduction=len(ex["terms"])-len(terms),block_first=ex["first"],block_last_exclusive=ex["last"])
        row["distinct_output_directions"]=len({term[2] for term in ex["terms"]})
        row["distinct_control_functions"]=len({factor for term in ex["terms"] for factor in term[:2]})
        terms,linears,rank_stats=quadratic_rank_decomposition(terms,linears)
        terms,linears=reduce_terms(terms,linears)
        row["same_output_quadratic_groups"]=rank_stats
        row["after_quadratic_rank_products"]=len(terms)
        checked=moves=0;timed_out=False
        while True:
            terms,linears,n,improved,timed_out=try_one_flip(terms,linears,deadline)
            checked+=n
            if not improved:break
            moves+=1
        row.update(flip_candidates_checked=checked,successful_flip_moves=moves,time_limit_reached=timed_out,ccx_removed=len(ex["terms"])-len(terms),new_core_products=len(terms),linear_updates=len(linears))
        if row["ccx_removed"]:
            candidate=km.Circuit(synthesize(ex,terms,linears))
            previous=words[:,5*(k-1):5*k] if k else zero
            current=words[:,5*k:5*(k+1)]
            row["proofs"]=[prove_one(candidate,previous,current,address_bits,f"joint k={k}/forward"),prove_one(candidate,current,previous,address_bits,f"joint k={k}/reverse")]
            row["candidate_ccx"]=int(candidate.operation_statistics().num_toffoli_like)
            assert row["candidate_ccx"]==row["source_ccx"]-row["ccx_removed"]
            assert candidate.num_qubits<=128
            row["candidate_qubits"]=candidate.num_qubits
            row["status"]="EXACT_REACHABLE_CANDIDATE_PASS"
        else:
            candidate=source;row["status"]="NO_REDUCTION_IN_CLASS"
            # A zero-hit result is only useful if frame extraction is sound.
            # Rebuild the unoptimized products in the exit frame and prove the
            # complete normalized circuit independently in both directions.
            normalized=km.Circuit(synthesize(ex,ex["terms"],[]))
            previous=words[:,5*(k-1):5*k] if k else zero
            current=words[:,5*k:5*(k+1)]
            row["normalization_proofs"]=[prove_one(normalized,previous,current,address_bits,f"normalized k={k}/forward"),prove_one(normalized,current,previous,address_bits,f"normalized k={k}/reverse")]
            assert int(normalized.operation_statistics().num_toffoli_like)==row["source_ccx"]
            row["normalization_preserves_ccx_and_qubits"]=normalized.num_qubits==source.num_qubits
            assert row["normalization_preserves_ccx_and_qubits"]
        rows.append(row);candidates.append(candidate)
        print(json.dumps({key:row[key] for key in ["k","status","core_products","ccx_removed","flip_candidates_checked","successful_flip_moves"]}),flush=True)
        if timed_out:break
    reduction=sum(row["ccx_removed"] for row in rows)
    report={"status":"CANDIDATE_EXACT_PASS" if reduction else "NO_REDUCTION_IN_BOUNDED_CLASS","scope":"same-entry-frame product merges; exact Boolean quadratic-rank decomposition per identical output direction; one shared-factor XOR flip followed by an immediate two-factor merge, greedily repeated after improvements","table_sha256":hashlib.sha256(args.table.read_bytes()).hexdigest(),"script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"loaders":rows,"ccx_removed_per_pass":reduction,"all_15_loaders_processed":len(rows)==15,"extracted_core_products":sum(row.get("core_products",0) for row in rows),"normalized_circuits_exactly_proved":sum("normalization_proofs" in row for row in rows),"source_files_modified":False,"official_score_verifier_run":False}
    if reduction:
        assert len(rows)==15,"Do not publish an incomplete family"
        args.output_dir.mkdir()
        proof_count=0
        for k,candidate in enumerate(candidates):
            previous=words[:,5*(k-1):5*k] if k else zero;current=words[:,5*k:5*(k+1)]
            prove_one(candidate,previous,current,address_bits,f"family k={k}/forward")
            prove_one(candidate,current,previous,address_bits,f"family k={k}/reverse")
            proof_count+=2440
            path=args.output_dir/f"angle_k_{k}.kmb";candidate.to_file(path,format="kmb")
            rows[k]["candidate_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        shutil.copyfile(args.table,args.output_dir/"submission.npz")
        report.update(candidate_directory=str(args.output_dir),exact_address_transition_cases=proof_count,derived_total_toffoli_same_geometry=14728-2*reduction,derived_total_qubits_same_geometry=427)
    report.update(seconds=time.monotonic()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="loaders"},indent=2))


if __name__=="__main__":main()
