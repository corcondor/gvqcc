#!/usr/bin/env python3
"""Extract zero-Toffoli nonlinear angle masks from adjacent ANGLE feature spans.

Only high-address functions constant within each 16-address block are used.
Every mask is represented by live wires after the output-product block in
both adjacent loaders.  Its forward/backward target propagation is verified
separately when materializing a candidate.
"""
from pathlib import Path
import hashlib,itertools,json,time
import numpy as np
import kickmix as km
from chemistry_joint_product_resynthesis import extract,DATA,DATA_INDEX
from chemistry_dontcare_v4_prune import basis_state,mutate,suffix_directions
from chemistry_reachable_exact_proof import pack

ROOT=Path('/workspace/scratch/3815fb5fae06')
SOURCE=Path('/workspace/scratch/7f542e06b7cf/dqi_inputs/chemistry_4033')
TABLE=ROOT/'score6_chem/transfer_full/submission.npz'

def basis(items):
    result={}
    for value,representation in items:
        while value:
            bit=value.bit_length()-1
            if bit in result:
                v,r=result[bit];value^=v;representation^=r
            else:
                result[bit]=(value,representation);break
    return result

def expression(value,base):
    representation=0
    while value:
        bit=value.bit_length()-1
        if bit not in base:return None
        v,r=base[bit];value^=v;representation^=r
    return representation

def high_table(truth,count=1220):
    out=0
    for h in range((count+15)//16):
        lo=16*h;n=min(16,count-lo);bits=(truth>>lo)&((1<<n)-1)
        if bits not in (0,(1<<n)-1):return None
        if bits:out|=1<<h
    return out

def extract_live(k,words,abits):
    circuit=km.Circuit.from_file(SOURCE/f'angle_k_{k}.kmb')
    ex=extract(circuit);ones=(1<<len(words))-1
    state=basis_state(circuit,words[:,5*(k-1):5*k],abits)
    for line in ex['lines'][:ex['last']]:mutate(state,line,ones)
    items=[];quotient={}
    # Pure high functions may be XORs of wires containing both high and low
    # components; filtering individual wires would lose valid free masks.
    for q in ex['pool']+[circuit.num_qubits]:
        full=state[q] if q<circuit.num_qubits else ones
        representative=sum(((full>>(a&~15))&1)<<a for a in range(len(words)))
        residual=full^representative;physical=1<<q
        while residual:
            bit=residual.bit_length()-1
            if bit in quotient:
                rr,ff,pp=quotient[bit];residual^=rr;full^=ff;physical^=pp
            else:quotient[bit]=(residual,full,physical);break
        if not residual:
            table=high_table(full);assert table is not None
            if table:items.append((table,physical))
    base=basis(items)
    # Map an insertion on any DATA bit to its final 40-bit output direction.
    final=suffix_directions(ex,circuit)
    directions=[]
    for q in DATA:
        out=sum(1<<j for j,f in enumerate(final) if (f>>DATA_INDEX[q])&1)
        directions.append((out,1<<q))
    db=basis(directions)
    target={str(j):expression(1<<j,db) for j in range(40) if j%8<6}
    assert all(x is not None for x in target.values())
    return dict(batch=k,qubits=circuit.num_qubits,last=ex['last'],basis=base,
        live_rank=len(base),target_directions=target,source_sha256=hashlib.sha256((SOURCE/f'angle_k_{k}.kmb').read_bytes()).hexdigest())

def main():
    start=time.monotonic();data=dict(np.load(TABLE));words=data['angle_words'].astype(np.uint64)
    addresses=np.arange(len(words),dtype=np.uint64);abits=[pack((addresses>>b)&1) for b in range(11)]
    live={k:extract_live(k,words,abits) for k in range(1,15)}
    masks=[];stats=[]
    # Low-weight common codewords are more useful than a dense nullspace basis:
    # they perturb only 16, 32, or 48 actual vector rows, with no one-body rows.
    for k in range(1,15):
        ba=live[k]['basis'];bb=live[k+1]['basis'] if k<14 else ba
        candidates=[];hist={}
        for weight in (1,2,3):
            for hs in itertools.combinations(range(5,77),weight):
                truth=sum(1<<h for h in hs)
                a=expression(truth,ba)
                if a is None:continue
                b=expression(truth,bb)
                if b is None:continue
                candidates.append(dict(batch=k,groups=list(hs),truth_hex=hex(truth),
                    controls_current_hex=hex(a),controls_next_hex=hex(b) if k<14 else None))
                hist[str(weight)]=hist.get(str(weight),0)+1
        masks.extend(candidates)
        row=dict(batch=k,rank_current=live[k]['live_rank'],rank_next=live[k+1]['live_rank'] if k<14 else None,
            common_masks_by_weight=hist,total=len(candidates));stats.append(row);print(json.dumps(row),flush=True)
    serial_live={str(k):{**{n:v for n,v in d.items() if n!='basis'},'basis':{str(p):[hex(v),hex(r)] for p,(v,r) in d['basis'].items()},'target_directions':{j:hex(v) for j,v in d['target_directions'].items()}} for k,d in live.items()}
    # Keep the full mask space compact; control expressions are reconstructed
    # exactly from the saved live bases for the numerical shortlist.
    mask_path=Path(__file__).with_suffix('.npz')
    packed_masks=np.full((len(masks),4),255,dtype=np.uint8)
    for i,row in enumerate(masks):
        packed_masks[i,0]=row['batch'];packed_masks[i,1:1+len(row['groups'])]=row['groups']
    np.savez_compressed(mask_path,masks=packed_masks)
    report=dict(status='EXACT_COMMON_FEATURE_SPANS_EXTRACTED',table=str(TABLE),table_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest(),
        source=str(SOURCE),live=serial_live,mask_path=str(mask_path),statistics=stats,total_masks=len(masks),seconds=time.monotonic()-start,
        numerical_optimization_run=False,full_circuit_verified=False)
    p=Path(__file__).with_suffix('.json');p.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'live','masks','statistics'}}),flush=True)

if __name__=='__main__':main()
