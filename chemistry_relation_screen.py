#!/usr/bin/env python3
"""Actual-domain nonlinear-product dependencies and MBU opportunities.

Tests the union of both reachable batch inputs. This is not the earlier search
for one CCX product in a linear span: it also tests the post-CCX target for
measurement-based erasure and all linear dependencies among output products
modulo the whole entry control-function space.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import kickmix as km
import numpy as np

from chemistry_affine_span_resynthesis import basis_expression, parse_line
from chemistry_joint_product_resynthesis import extract, synthesize
from chemistry_reachable_exact_proof import pack, prove_one


def initial_values(circuit,previous,current):
    incoming=np.concatenate([previous,current],axis=0)
    address=np.tile(np.arange(len(previous),dtype=np.uint64),2)
    values=[0]*circuit.num_qubits
    for q in range(11):values[q]=pack((address>>q)&1)
    for j in range(5):
        for bit in range(8):values[11+8*j+bit]=pack((incoming[:,j]>>bit)&1)
    return values,(1<<len(incoming))-1


def advance(values,gate,qs,one):
    if gate=="X":values[qs[0]]^=one
    elif gate=="CX":values[qs[1]]^=values[qs[0]]
    elif gate=="CCX":values[qs[2]]^=values[qs[0]]&values[qs[1]]
    elif gate in {"HMR","R"}:values[qs[0]]=0


def reduce_value(basis,value):
    expression=0
    while value:
        pivot=value.bit_length()-1
        if pivot not in basis:return value,expression
        row,support=basis[pivot];value^=row;expression^=support
    return 0,expression


def insert(basis,value,expression):
    while value:
        pivot=value.bit_length()-1
        if pivot not in basis:
            basis[pivot]=(value,expression);return True
        row,support=basis[pivot];value^=row;expression^=support
    return False


def evaluate_form(form,values,one):
    value=one if form&1 else 0
    for q in range(len(values)):
        if form>>(q+1)&1:value^=values[q]
    return value


def scan(circuit,previous,current):
    values,one=initial_values(circuit,previous,current)
    try:ex=extract(circuit)
    except ValueError as exc:ex=None;extract_error=str(exc)
    mbu=[]; entry=None; nccx=0
    for index,line in enumerate(str(circuit).splitlines()):
        if ex is not None and index==ex["first"]:entry=list(values)
        gate,qs,condition=parse_line(line)
        if gate=="CCX":
            assert condition is None
            nccx+=1
            a,b,target=qs
            after=values[target]^(values[a]&values[b])
            witness=basis_expression(values,after,target,one)
            if witness is not None:
                mbu.append({"line_index":index,"gate":line,"post_target_linear_witness":str(witness),"zero_after_gate":after==0})
        advance(values,gate,qs,one)
    result={"source_ccx":nccx,"measurement_uncompute_opportunities":mbu}
    if ex is None:
        result["product_block_status"]=extract_error
        return result,None
    basis={};n=len(entry)
    insert(basis,one,1<<n)
    for q in ex["pool"]:insert(basis,entry[q],1<<q)
    base_rank=len(basis)
    independent=[]; relations=[]; coefficients={};linear_coefficients={}
    for i,(u,v,w) in enumerate(ex["terms"]):
        product=evaluate_form(u,entry,one)&evaluate_form(v,entry,one)
        remaining,witness=reduce_value(basis,product)
        if remaining:
            independent.append(i)
            insert(basis,product,1<<(n+1+i))
            expression=1<<(n+1+i)
        else:
            expression=witness
            relations.append({"product":i,"free_wires":[q for q in range(n) if witness>>q&1],"constant":bool(witness>>n&1),"other_products":[j for j in independent if witness>>(n+1+j)&1]})
        for q in range(n+1):
            if expression>>q&1:linear_coefficients[q]=linear_coefficients.get(q,0)^w
        for j in independent:
            if expression>>(n+1+j)&1:coefficients[j]=coefficients.get(j,0)^w
    new_terms=[(ex["terms"][i][0],ex["terms"][i][1],w) for i,w in coefficients.items() if w]
    linears=[((1 if q==n else 1<<(q+1)),w) for q,w in linear_coefficients.items() if w]
    result.update(product_block_status="EXACT_ACTUAL_DOMAIN_QUOTIENT_COMPLETE",core_products=len(ex["terms"]),entry_control_function_rank=base_rank,nonlinear_product_quotient_rank=len(independent),dependent_products=relations,new_core_products=len(new_terms),product_reduction=len(ex["terms"])-len(new_terms))
    text=synthesize(ex,new_terms,linears) if len(new_terms)<len(ex["terms"]) else None
    return result,text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders",type=Path,required=True)
    parser.add_argument("--table",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists() or args.output_dir.exists():raise FileExistsError("Use fresh output paths")
    started=time.monotonic()
    with np.load(args.table,allow_pickle=False) as data:words=data["angle_words"].astype(np.uint64)
    assert words.shape==(1220,75)
    zero=np.zeros((1220,5),dtype=np.uint64);address=np.arange(1220,dtype=np.uint64)
    address_bits=[pack((address>>q)&1) for q in range(11)]
    rows=[];candidates=[]
    for k in range(15):
        path=args.loaders/f"angle_k_{k}.kmb";circuit=km.Circuit.from_file(path)
        previous=words[:,5*(k-1):5*k] if k else zero;current=words[:,5*k:5*(k+1)]
        row,text=scan(circuit,previous,current)
        row.update(k=k,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if text:
            candidate=km.Circuit(text)
            row["proofs"]=[prove_one(candidate,previous,current,address_bits,f"relation k={k}/forward"),prove_one(candidate,current,previous,address_bits,f"relation k={k}/reverse")]
            row["candidate_ccx"]=int(candidate.operation_statistics().num_toffoli_like)
            row["candidate_qubits"]=candidate.num_qubits
            assert candidate.num_qubits<=128
            assert row["candidate_ccx"]==row["source_ccx"]-row["product_reduction"]
        else:candidate=circuit
        candidates.append(candidate);rows.append(row)
        print(json.dumps({key:row.get(key) for key in ["k","source_ccx","core_products","entry_control_function_rank","nonlinear_product_quotient_rank","product_reduction"]}|{"mbu_opportunities":len(row["measurement_uncompute_opportunities"])}),flush=True)
    reduction=sum(row.get("product_reduction",0) for row in rows)
    report={"status":"EXACT_PRODUCT_QUOTIENT_CANDIDATE" if reduction else "NO_PRODUCT_QUOTIENT_REDUCTION","domain":"1220 addresses times exact previous/current batches simultaneously","script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"table_sha256":hashlib.sha256(args.table.read_bytes()).hexdigest(),"loaders":rows,"ccx_removed_per_pass":reduction,"measurement_uncompute_opportunities":sum(len(row["measurement_uncompute_opportunities"]) for row in rows),"source_files_modified":False,"official_verifier_run":False}
    if reduction:
        args.output_dir.mkdir()
        for k,candidate in enumerate(candidates):
            previous=words[:,5*(k-1):5*k] if k else zero;current=words[:,5*k:5*(k+1)]
            prove_one(candidate,previous,current,address_bits,f"family k={k}/forward")
            prove_one(candidate,current,previous,address_bits,f"family k={k}/reverse")
            path=args.output_dir/f"angle_k_{k}.kmb";candidate.to_file(path,format="kmb")
            rows[k]["candidate_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        report.update(exact_transitions=36600,candidate_directory=str(args.output_dir),derived_total_toffoli=14728-2*reduction,derived_total_qubits=427)
    report.update(seconds=time.monotonic()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="loaders"},indent=2))


if __name__=="__main__":main()
