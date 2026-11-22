"""Exact native-KMB warm-start recovery for QDLN (KickMix circuit format v2).

Recover the 82 precomputed AND-cache gates as an immutable source bank, then
symbolically track full 128-wire CX transformations and all noncache AND
effects until the first HMR. This creates a parent-preserving, nonlinear
feature dictionary for the differentiable learner.

Strictly a pre-HMR circuit analysis, NOT full phase verification.
"""
from __future__ import annotations
import json
import struct
from pathlib import Path

MAGIC=bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")

def read_kmb(path):
    data=Path(path).read_bytes()
    if data[:16]!=MAGIC:
        raise ValueError("Invalid KickMix KMB magic")
    ver,nqubits,nbits,nregs=struct.unpack_from("<4I",data,16)
    if ver!=2:raise ValueError("Requires KMB v2")
    keys=("ops","qqq","qq","q","b","c","angle","info_tags","info_tag_chars")
    counts=dict(zip(keys,struct.unpack_from("<9Q",data,32)))
    pos=104
    for _ in range(nregs):
        typ,size=struct.unpack_from("<2Q",data,pos)
        assert typ==0
        pos+=16+size
    sizes=[(counts["ops"],1),(counts["qqq"],4),(counts["qqq"],4),
           (counts["qqq"],4),(counts["qq"],4),(counts["qq"],4),
           (counts["q"],4),(counts["b"],4),(counts["c"],4)]
    streams=[]
    for typ,(n,width) in enumerate(sizes,1):
        packet,size=struct.unpack_from("<2Q",data,pos)
        assert packet==typ and size==n*width
        pos+=16
        if width==1:values=data[pos:pos+n]
        else:values=struct.unpack_from(f"<{n}I",data,pos)
        streams.append(values);pos+=size
    ops,q30,q31,q32,q20,q21,q10,b0,bc=streams
    p3=p2=p1=0;instructions=[]
    for op in ops:
        kind=op&0x30
        if kind==0x30:
            instructions.append((op,(q30[p3],q31[p3],q32[p3])));p3+=1
        elif kind==0x20:
            instructions.append((op,(q20[p2],q21[p2])));p2+=1
        elif kind==0x10:
            instructions.append((op,(q10[p1],)));p1+=1
        else:instructions.append((op,()))
    assert p3==counts["qqq"] and p2==counts["qq"] and p1==counts["q"]
    return nqubits,counts,instructions

def extract_pre_hmr(instructions,nqubits,cache_ccx=82):
    """Return exact output-product factors as GF(2) masks over cached wires.

    Proof condition: no nonlinear output-product result can influence a later
    AND control. If present, reject rather than silently linearizing it.
    """
    state=[1<<j for j in range(nqubits)]
    paid=0;terms=[];fail=[];start=end=None
    for op_i,(op,qs) in enumerate(instructions):
        if op==0x50:
            end=op_i;break
        if op==0x31:
            paid+=1
            if paid==cache_ccx+1:
                start=op_i
                state=[1<<j for j in range(nqubits)]
            if paid<=cache_ccx:continue
            a,b,t=qs
            if (state[a]|state[b])>>nqubits:
                fail.append(op_i)
            terms.append({"op":op_i,"a":str(state[a]),"b":str(state[b]),"target":t})
            state[t]^=1<<(nqubits+len(terms)-1)
        elif op==0x21:
            a,b=qs;state[b]^=state[a]
        elif op in (0x11,0x00,0x06):
            pass
        else:
            raise ValueError(("Unsupported operation before first HMR",op_i,op))
    if start is None or end is None:raise ValueError("Missing product segment or HMR")
    for j,term in enumerate(terms):
        term["effect"]=str(sum(1<<q for q,v in enumerate(state) if (v>>(nqubits+j))&1))
    return {"qubits":nqubits,"pre_hmr_paid":paid,"cache_ccx":cache_ccx,
            "first_product_op":start,"first_hmr_op":end,
            "paid_tail":len(terms),"nonlinear_feedback_sites":fail,
            "formal_parent_exact":not fail,"terms":terms}

def gf2_rank(vectors):
    piv={}
    for x in vectors:
        while x:
            p=x.bit_length()-1
            if p in piv:x^=piv[p]
            else:piv[p]=x;break
    return len(piv)

def output_witness(effects,offset=11,width=35):
    """Find output XOR mask w that selects all given effect vectors."""
    piv={}
    for e in effects:
        v=(e>>offset)&((1<<width)-1);rhs=1
        while v:
            p=v.bit_length()-1
            if p in piv:
                a,b=piv[p];v^=a;rhs^=b
            else:piv[p]=(v,rhs);break
        if not v and rhs:return None
    w=0
    for p in sorted(piv):
        v,rhs=piv[p]
        if rhs^(((v&~(1<<p))&w).bit_count()&1):w|=1<<p
    assert all(((w&(e>>offset)).bit_count()&1) for e in effects)
    return w

def polar_rank(terms,w,nqubits=128,output_offset=11):
    """GF(2) alternating polar matrix for a selected output XOR sum."""
    rows=[0]*nqubits
    for term in terms:
        if not ((int(term["effect"])>>(output_offset)&w).bit_count()&1):
            continue
        a,b=int(term["a"]),int(term["b"])
        if (a|b)>>nqubits:raise ValueError("Nonlinear input control")
        ai=[i for i in range(nqubits) if a>>i&1]
        bj=[j for j in range(nqubits) if b>>j&1]
        for i in ai:
            for j in bj:
                if i!=j:
                    rows[i]^=1<<j
                    rows[j]^=1<<i
    rank=gf2_rank(rows)
    assert rank%2==0
    return rank

def lower_bound(analysis,ids):
    if analysis["nonlinear_feedback_sites"]:
        raise ValueError("Formal paid-tail decomposition not applicable")
    terms=[analysis["terms"][i] for i in ids]
    w=output_witness([int(t["effect"]) for t in terms])
    if w is None:return None
    rank=polar_rank(terms,w,analysis["qubits"])
    return {"chosen_terms":len(terms),"output_mask":w,
            "polar_rank":rank,"min_AND":rank//2,
            "saturates_formal_bound":rank//2==len(terms),
            "scope":"independent cached-wire formal inputs ONLY"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("kmb")
    p.add_argument("--cache-ccx",type=int,default=82)
    p.add_argument("--out")
    args=p.parse_args()
    n,c,ops=read_kmb(args.kmb)
    data=extract_pre_hmr(ops,n,args.cache_ccx)
    if args.out:Path(args.out).write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data.items() if k!="terms"},indent=2))

if __name__=="__main__":main()
