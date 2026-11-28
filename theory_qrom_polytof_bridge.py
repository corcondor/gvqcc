#!/usr/bin/env python3
"""Bridge structured ANGLE accumulation blocks to Polytof COMM tensors.

Only the two control factors may mix. The output factor remains separate, so
the reconstructed circuit uses X/CX/CCX and requires no unsupported Hadamard.
The optimizer preserves the quadratic tensor. We explicitly restore all
Boolean diagonal and affine corrections, then independently prove both
reachable input-batch directions and every measurement-phase coefficient.
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
from chemistry_joint_product_resynthesis import extract, synthesize, product_anf
from chemistry_reachable_exact_proof import pack, prove_one


def bits(x):
    while x:
        b = x & -x
        yield b.bit_length()-1
        x ^= b


def polynomial(terms):
    result={}
    for a,b,w in terms:
        for m in product_anf(a,b):
            result[m]=result.get(m,0)^w
    return {m:w for m,w in result.items() if w}


def term_encode(terms,pool):
    positions={q+1:i for i,q in enumerate(pool)}
    def convert(x):
        return sum(1<<positions[i] for i in bits(x & ~1))
    encoded=[(convert(a),convert(b),w) for a,b,w in terms]
    return encoded


def write_pool(path,terms):
    mask=(1<<64)-1
    row=[part for term in terms for x in term for part in (x & mask,x>>64)]
    np.save(path,np.array([row],dtype=np.uint64))


def load_pool(path):
    row=np.load(path,allow_pickle=False)[0]
    if row.ndim!=1 or len(row)%6:raise ValueError("Not a VEC_WORDS=2 COMM pool")
    vectors=[int(row[i])|(int(row[i+1])<<64) for i in range(0,len(row),2)]
    terms=[]
    for i in range(0,len(vectors),3):
        a,b,w=vectors[i:i+3]
        if a and b and a!=b and w:terms.append((a,b,w))
    return terms


def tensor(terms, n):
    p=polynomial([(a<<1,b<<1,w) for a,b,w in terms])
    triples=[]
    for m,w in p.items():
        if m.bit_count()!=2:continue
        i,j=list(bits(m))
        triples.extend((i-1,j-1,k) for k in bits(w))
    triples.sort()
    return np.array([(n,n,35)]+triples,dtype=np.int64)


def prepare(args):
    rows=[]
    for k in args.batches:
        path=args.loaders/f"angle_k_{k}.kmb"
        c=km.Circuit.from_file(path);e=extract(c)
        terms=term_encode(e['terms'],e['pool']); n=len(e['pool'])
        data=tensor(terms,n)
        tid=9100+k
        tpath=args.workspace/'data'/'tensors'/f'{tid:04d}.npy'
        ppath=args.workspace/'data'/'cpd'/'comm'/f'{tid:04d}-{len(terms):05d}.npy'
        tpath.parent.mkdir(parents=True,exist_ok=True);ppath.parent.mkdir(parents=True,exist_ok=True)
        np.save(tpath,data);write_pool(ppath,terms)
        sums={}
        repeated=0
        for i,(a,b,w) in enumerate(terms):
            for v in (a,b,a^b):
                if v in sums and sums[v]!=i:repeated+=1
                sums[v]=i
        row={'batch':k,'tensor_id':tid,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'source_qubits':c.num_qubits,'core_products':len(terms),'control_dimension':n,
             'tensor_nonzero_entries':len(data)-1,'commutative_shared_factors':repeated,
             'input_pool_path':str(ppath),'tensor_path':str(tpath)}
        rows.append(row);print(json.dumps(row),flush=True)
    return {'status':'COMM_TENSORS_PREPARED','loaders':rows,
            'gate_model':'X/CX/CCX only for output accumulation; arbitrary control inputs; diagonal terms retained during import',
            'polytof_source':'https://github.com/ZIB-IOL/polytof','paper':'https://arxiv.org/abs/2602.15285v2'}


def verify(args):
    with np.load(args.table,allow_pickle=False) as data:words=data['angle_words'].astype(np.uint64)
    address=np.arange(len(words),dtype=np.uint64)
    address_bits=[pack((address>>q)&1) for q in range(11)]
    rows=[]
    for k in args.batches:
        src=args.loaders/f'angle_k_{k}.kmb';c=km.Circuit.from_file(src);e=extract(c)
        paths=sorted((args.workspace/'data'/'cpd'/'comm').glob(f'{9100+k:04d}-*.npy'))
        if not paths:raise FileNotFoundError(k)
        ppath=min(paths,key=lambda p:int(p.stem.split('-')[1]))
        raw=load_pool(ppath)
        def convert(x):return sum(1<<(e['pool'][i]+1) for i in bits(x))
        terms=[(convert(a),convert(b),w) for a,b,w in raw]
        original=polynomial(e['terms']);replaced=polynomial(terms)
        correction={m:original.get(m,0)^replaced.get(m,0) for m in original.keys()|replaced.keys()}
        correction={m:w for m,w in correction.items() if w}
        if any(m.bit_count()>1 for m in correction):raise AssertionError('Quadratic tensor mismatch')
        linears=[(m or 1,w) for m,w in correction.items()]
        candidate=km.Circuit(synthesize(e,terms,linears))
        previous=words[:,5*(k-1):5*k]
        current=words[:,5*k:5*(k+1)]
        proofs=[prove_one(candidate,previous,current,address_bits,f'k{k}/forward'),
                prove_one(candidate,current,previous,address_bits,f'k{k}/reverse')]
        before=str(c).count('\nCCX ');after=str(candidate).count('\nCCX ')
        row={'batch':k,'source_ccx':before,'candidate_ccx':after,'ccx_removed':before-after,
             'source_qubits':c.num_qubits,'candidate_qubits':candidate.num_qubits,'pool_path':str(ppath),
             'linear_correction_terms':len(linears),'exact_proofs':proofs}
        if before>after:
            if args.output_dir is None:raise ValueError('Need output directory for improvement')
            args.output_dir.mkdir(parents=True,exist_ok=True)
            dst=args.output_dir/src.name;candidate.to_file(dst,format='kmb')
            row.update(candidate_path=str(dst),candidate_sha256=hashlib.sha256(dst.read_bytes()).hexdigest())
        rows.append(row);print(json.dumps({x:v for x,v in row.items() if x!='exact_proofs'}),flush=True)
    return {'status':'EXACT_VERIFIED','loaders':rows,'total_ccx_removed':sum(x['ccx_removed'] for x in rows),
            'source_files_modified':False,'official_scoring_run':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','verify'])
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--table',type=Path)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--output-dir',type=Path)
    p.add_argument('--batches',type=int,nargs='+',default=list(range(1,15)))
    args=p.parse_args();t=time.monotonic()
    if args.report.exists():raise FileExistsError(args.report)
    result=prepare(args) if args.mode=='prepare' else verify(args)
    result.update(seconds=time.monotonic()-t,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.report.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
