#!/usr/bin/env python3
"""Prove linear independence of current product dictionary modulo free wires.

Uses exact truth tables on the valid address domain, including nonlinear
relations among prepared feature wires. This is stronger than treating the
feature wires as independent formal variables. It does not bound a synthesis
that introduces new control products.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import kickmix as km
from chemistry_joint_product_resynthesis import extract,TAGS
from chemistry_affine_span_resynthesis import parse_line
from theory_qrom_prefix_bound import rank


def analyze(path):
    c=km.Circuit.from_file(path);e=extract(c);one=(1<<1220)-1;s=[0]*c.num_qubits
    for q in range(11):s[q]=sum(((a>>q)&1)<<a for a in range(1220))
    for q,(i,j) in zip(sorted(TAGS),[(0,1),(0,2),(1,2),(0,3),(1,3)]):s[q]=s[i]&s[j]
    start=next(i for i,l in enumerate(e['lines']) if parse_line(l)[0]=='R')
    for line in e['lines'][start:e['first']]:
        gate,q,_=parse_line(line)
        if gate=='CX':s[q[1]]^=s[q[0]]
        elif gate=='CCX':s[q[2]]^=s[q[0]]&s[q[1]]
        elif gate=='X':s[q[0]]^=one
        elif gate!='R':raise AssertionError(gate)
    def evaluate(a):
        v=one if a&1 else 0
        for q in e['pool']:
            if a>>(q+1)&1:v^=s[q]
        return v
    base=[one]+[s[q] for q in e['pool']]
    products=[evaluate(a)&evaluate(b) for a,b,w in e['terms']]
    r0=rank(base);r1=rank(base+products)
    assert r1-r0==len(products)
    assert all(w for _,_,w in e['terms'])
    return {'batch':int(path.stem.split('_')[-1]),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'feature_span_rank':r0,'feature_plus_products_rank':r1,
            'products':len(products),'quotient_rank':r1-r0,'all_product_output_directions_nonzero':True,
            'deletable_existing_products_under_global_xor_recombination':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();t=time.monotonic()
    if args.report.exists():raise FileExistsError(args.report)
    rows=[analyze(args.loaders/f'angle_k_{k}.kmb') for k in range(1,15)]
    report={'status':'EXACT_FIXED_PRODUCT_DICTIONARY_LOWER_BOUND','loaders':rows,
            'total_products':sum(r['products'] for r in rows),'valid_addresses':1220,
            'scope':'Fixed prepared-feature space V and fixed linear input/output skeleton; accumulation with the existing product dictionary. The 35 incoming data-wire functions are not extra free resources.',
            'proof':'Modulo the free span V of constant and prepared feature functions, all original products p_i are independent. Each has nonzero output direction w_i. Hence the vector function sum_i p_i w_i has a unique representation in this dictionary modulo V and requires every p_i. This includes arbitrary multi-product XOR recombination, not only pairwise matches.',
            'limitation':'New products, changed feature maps, nonlinear resynthesis, changed angle encoding and other whole-loader architectures remain outside this lower bound.',
            'seconds':time.monotonic()-t,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
