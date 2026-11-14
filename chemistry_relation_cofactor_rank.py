#!/usr/bin/env python3
"""Joint-output synthesis bound from 16-row high/low cofactor matrices.

Uses the real four low address bits and the five canonical conserved tags.
For each output combination of Hamming weight at most three, measures the
rank of its high-address by low-address cofactor matrix, then chooses a
minimum-weight basis from this finite candidate set. Two rank-one bilinear
terms can be packed into one AND, with high-only/low-only corrections.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import resource
import time

import kickmix as km

from chemistry_affine_span_resynthesis import parse_line
from chemistry_joint_product_resynthesis import DATA, extract
from chemistry_relation_screen import advance,evaluate_form


def rank(vectors):
    basis={}
    for value in vectors:
        while value:
            pivot=value.bit_length()-1
            if pivot not in basis:
                basis[pivot]=value;break
            value^=basis[pivot]
    return len(basis)


def analyze(path,coded_parities=False):
    circuit=km.Circuit.from_file(path);ex=extract(circuit)
    count=2048;one=(1<<count)-1;values=[0]*circuit.num_qubits
    for q in range(11):values[q]=sum(1<<a for a in range(count) if a>>q&1)
    pairs=[(0,1),(0,2),(1,2),(0,3),(1,3)]
    for j,(a,b) in enumerate(pairs):values[11+8*j+7]=values[a]&values[b]
    for line in ex["lines"][:ex["first"]]:
        gate,qs,condition=parse_line(line);advance(values,gate,qs,one)
    output=[0]*len(DATA);low_planes=defaultdict(list);low_forms=[]
    for i,(u,v,w) in enumerate(ex["terms"]):
        fu=evaluate_form(u,values,one);fv=evaluate_form(v,values,one)
        product=fu&fv
        for j in range(len(DATA)):
            if w>>j&1:output[j]^=product
        low=[]
        for f in [fu,fv]:
            lo=(f&65535)^(65535 if f&1 else 0)
            assert all(((f>>(16*h))&65535)==lo^(65535 if f>>(16*h)&1 else 0) for h in range(77))
            low.append(lo);low_forms.append(lo)
        a,b=low
        low_planes[tuple(sorted([a,b,a^b]))].append(w)
    matrices=[]
    for f in output:
        first=f&65535
        columns=[]
        for low in range(1,16):
            column=0
            for high in range(77):
                bit=((f>>(16*high+low))^(f>>(16*high))^(first>>low)^first)&1
                column|=bit<<high
            columns.append(column)
        matrices.append(columns)
    options=[];histogram=Counter();light=[(0,[0]*15)];seen=set()
    for size in range(1,4):
        for indices in itertools.combinations(range(len(DATA)),size):
            columns=[0]*15
            for index in indices:
                columns=[a^b for a,b in zip(columns,matrices[index])]
            r=rank(columns);mask=sum(1<<i for i in indices)
            options.append(((r+1)//2,mask,r));histogram[r]+=1
            seen.add(mask)
            if size<=2:light.append((mask,columns))
    if coded_parities:
        # Include the five-word parity identities present in the actual coded
        # angle table, not only low-Hamming-weight arbitrary bit combinations.
        generators=[]
        for bit in range(7):
            mask=sum(1<<(7*word+bit) for word in range(5))
            columns=[0]*15
            for word in range(5):
                columns=[a^b for a,b in zip(columns,matrices[7*word+bit])]
            generators.append((mask,columns))
        parities=[(0,[0]*15)]
        for combination in range(1,128):
            bit=(combination&-combination).bit_length()-1
            previous=combination^(1<<bit)
            old_mask,old_columns=parities[previous]
            add_mask,add_columns=generators[bit]
            parities.append((old_mask^add_mask,[a^b for a,b in zip(old_columns,add_columns)]))
        for parity_mask,parity_columns in parities[1:]:
            for small_mask,small_columns in light:
                mask=parity_mask^small_mask
                if not mask or mask in seen:continue
                seen.add(mask)
                columns=[a^b for a,b in zip(parity_columns,small_columns)]
                r=rank(columns)
                options.append(((r+1)//2,mask,r));histogram[r]+=1
    options.sort()
    basis={};chosen=[]
    for cost,mask,r in options:
        value=mask
        while value:
            pivot=value.bit_length()-1
            if pivot not in basis:
                basis[pivot]=value;chosen.append({"output_combination":mask,"matrix_rank":r,"packed_ands":cost});break
            value^=basis[pivot]
        if len(basis)==len(DATA):break
    assert len(chosen)==len(DATA)
    measured=sum(row["packed_ands"] for row in chosen)
    original=len(ex["terms"])
    return {
        "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "core_products":original,
        "low_function_space_rank":rank(low_forms),
        "same_low_plane_groups":len(low_planes),
        "max_same_low_plane_products":max(map(len,low_planes.values())),
        "same_low_plane_output_rank_savings":sum(len(group)-rank(group) for group in low_planes.values()),
        "output_combinations_evaluated":len(options),
        "cofactor_rank_histogram":dict(sorted(histogram.items())),
        "coordinate_output_packed_ands":sum((rank(matrix)+1)//2 for matrix in matrices),
        "chosen_output_basis_packed_ands":measured,
        "packed_ands_delta_before_high_completion":measured-original,
        "basis":chosen,
        "potentially_better_before_high_completion":measured<original,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders",required=True,type=Path)
    parser.add_argument("--report",required=True,type=Path)
    parser.add_argument("--coded-parities",action="store_true")
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError("Use a fresh report path")
    started=time.monotonic();rows=[]
    for k in range(1,15):
        row={"k":k,**analyze(args.loaders/f"angle_k_{k}.kmb",args.coded_parities)};rows.append(row)
        print(json.dumps({key:row[key] for key in ["k","core_products","same_low_plane_output_rank_savings","coordinate_output_packed_ands","chosen_output_basis_packed_ands","packed_ands_delta_before_high_completion"]}),flush=True)
    report={
        "status":"COFACTOR_SYNTHESIS_SCREEN_COMPLETE",
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "address_geometry":"76 full blocks of 16 plus the four valid rows of block 76; for a conservative constructive bound the latter block is completed using the source gate functions",
        "canonical_tags":"(a0*a1,a0*a2,a1*a2,a0*a3,a1*a3)",
        "output_basis_candidate_class":"all nonzero combinations of 1, 2, or 3 of the 35 non-tag output bits"+("; plus the complete span of seven five-word bit-plane parities, XOR at most two individual output bits" if args.coded_parities else ""),
        "limitation":"This is a finite joint-output synthesis screen, not a globally optimal factorization. High-only correction functions may require one additional high-address helper; no circuit is emitted until a count improvement exists and those corrections are synthesized and verified.",
        "loaders":rows,
        "improving_batches_before_high_completion":[row["k"] for row in rows if row["potentially_better_before_high_completion"]],
        "candidate_files_written":False,
        "source_files_modified":False,
        "seconds":time.monotonic()-started,
        "peak_rss_mib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
    }
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="loaders"},indent=2))


if __name__=="__main__":main()
