#!/usr/bin/env python3
"""Exact GF(2) product-contribution rank for the two nonempty DC suffixes."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import kickmix as km
from chemistry_joint_product_resynthesis import extract
from chemistry_reachable_exact_proof import pack
from chemistry_dontcare_v4_prune import (
    SOURCE,TABLE,OUT,inactive_angles,basis_state,mutate,affine_value,suffix_directions,
)


def rank_and_dependencies(columns):
    basis={};dependencies=[]
    for n,v in enumerate(columns):
        combination=1<<n
        while v:
            lead=v.bit_length()-1
            if lead not in basis:
                basis[lead]=(v,combination);break
            old,which=basis[lead];v^=old;combination^=which
        if not v:dependencies.append([j for j in range(len(columns)) if combination>>j&1])
    return len(basis),dependencies


def main():
    start=time.monotonic();cpu=time.process_time()
    path=OUT/'chemistry_dontcare_v4_rank_results.json'
    if path.exists():raise FileExistsError(path)
    data=dict(np.load(TABLE,allow_pickle=False));words=data['angle_words'].astype(np.uint64)
    inactive=inactive_angles(words,data['tree_edges'])
    address=np.arange(1220,dtype=np.uint64);abits=[pack((address>>j)&1) for j in range(11)];ones=(1<<1220)-1
    rows=[]
    for k in (13,14):
        suffix=[pack(np.all(inactive[:,5*k+j::5],axis=1)) for j in range(5)]
        source=km.Circuit.from_file(SOURCE/f'angle_k_{k}.kmb');ex=extract(source)
        state=basis_state(source,words[:,5*(k-1):5*k],abits)
        for line in ex['lines'][:ex['first']]:mutate(state,line,ones)
        final=suffix_directions(ex,source);full=[];cared=[]
        for a,b,w in ex['terms']:
            p=affine_value(a,state,ones)&affine_value(b,state,ones)
            raw=projected=0
            for j,f in enumerate(final):
                if (f&w).bit_count()&1:
                    raw |= p << (1220*j)
                    allowed=suffix[j//8] if j%8<6 else 0
                    projected |= (p & (ones^allowed)) << (1220*j)
            full.append(raw);cared.append(projected)
        r0,d0=rank_and_dependencies(full);r1,d1=rank_and_dependencies(cared)
        rows.append(dict(batch=k,products=len(full),full_rank=r0,cared_rank=r1,
            full_nullity=len(full)-r0,cared_nullity=len(full)-r1,
            new_dependencies_from_dontcares=r0-r1,full_dependencies=d0,cared_dependencies=d1,
            suffix_inactive_by_slot=[x.bit_count() for x in suffix]))
    result=dict(status='RANK_AUDIT_COMPLETE',scope='Within-batch XOR subsets of original product contributions for k13 and k14; projected only onto cared outputs in all subsequent batches. No changes to control or output bases.',
        batches=rows,no_subset_deletion_candidate=all(not row['cared_dependencies'] for row in rows),
        source_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cpu_seconds=time.process_time()-cpu,elapsed_seconds=time.monotonic()-start,
        circuit_files_created=False,score_improvement_claimed=False)
    path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
