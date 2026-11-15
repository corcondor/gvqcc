#!/usr/bin/env python3
"""Exact rank-two sharing between several ANGLE output matrices."""
from argparse import ArgumentParser
from hashlib import sha256
import itertools
import json
from pathlib import Path
import random
import sys

import numpy as np
import kickmix as km

PIN = "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
J = 6
N = 1220

def bits(number):
    while number:
        bit = number & -number
        yield bit.bit_length()-1
        number ^= bit

def linear_combo(rows, coeff):
    value = 0
    for i in bits(coeff):
        value ^= rows[i]
    return value

def eliminate(rows):
    pivots, null = {}, []
    for i, row in enumerate(rows):
        representation = 1 << i
        while row:
            pivot = row.bit_length()-1
            if pivot not in pivots:
                pivots[pivot] = row, representation
                break
            old, coeff = pivots[pivot]
            row ^= old
            representation ^= coeff
        if not row:
            null.append(representation)
    return pivots, null

def reduce(pivots, value):
    coeff = 0
    for i in sorted(pivots, reverse=True):
        if value >> i & 1:
            row, rep = pivots[i]
            value ^= row
            coeff ^= rep
    return value, coeff

def intersection(rows, pivots):
    reduced = [reduce(pivots,v)[0] for v in rows]
    return [linear_combo(rows,z) for z in eliminate(reduced)[1]]

def solve_two(equations):
    """Solve dot(left, A)=rhs&1, dot(left, B)=rhs>>1."""
    echelon = {}
    for left, right in equations:
        while left:
            i = left.bit_length()-1
            if i not in echelon:
                echelon[i] = (left, right)
                break
            old, rhs = echelon[i]
            left ^= old
            right ^= rhs
        if not left and right:
            return None
    a = b = 0
    for i, (left, right) in sorted(echelon.items()):
        a |= ((right & 1) ^ ((left & a).bit_count() & 1)) << i
        b |= ((right >> 1) ^ ((left & b).bit_count() & 1)) << i
    return a,b

def rank_two_update(group, slices, basis_data, rng, attempts=6):
    first, *rest = group
    common = [v for v,_ in basis_data[first][0].values()]
    for index in rest:
        common = intersection(common, basis_data[index][0])
        if len(common)<2:
            return None
    kernels = [(v,0) for index in group for v in basis_data[index][1]]
    for attempt in range(attempts):
        if attempt==0:
            h0,h1=common[:2]
        else:
            i,j=rng.sample(range(1,1<<len(common)),2)
            h0,h1=linear_combo(common,i),linear_combo(common,j)
        equations=kernels.copy()
        for index in group:
            family=basis_data[index][0]
            r0,v0=reduce(family,h0)
            r1,v1=reduce(family,h1)
            assert not (r0 or r1)
            equations.extend(((v0,1),(v1,2)))
        uv=solve_two(equations)
        if uv is None:
            continue
        u0,u1=uv
        delta=[(h0 if u0>>r&1 else 0)^(h1 if u1>>r&1 else 0)
               for r in range(len(slices[first]))]
        output=0
        for index in group:
            before=len(basis_data[index][0])
            slices[index]=[old^change for old,change in zip(slices[index],delta)]
            basis_data[index]=eliminate(slices[index])
            assert len(basis_data[index][0])==before-2
            output |= 1<<index
        return u0,h1,u1,h0,output
    return None

def share(slices, rng, max_group):
    slices = [r.copy() for r in slices]
    subspaces = [eliminate(rows) for rows in slices]
    base_cost = sum((len(x[0])+1)//2 for x in subspaces)
    chosen = []
    for k in range(max_group,1,-1):
        while True:
            active = [i for i,b in enumerate(subspaces) if len(b[0])>=2]
            if len(active)<k:
                break
            rng.shuffle(active)
            active.sort(key=lambda n:-len(subspaces[n][0]))
            did_work=False
            # Highest-rank slices have the largest common subspaces. Try
            # both consecutive groups and bounded alternative groupings.
            consecutive=(tuple(active[j:j+k]) for j in range(0,len(active)-k+1,k))
            random_groups=(tuple(rng.sample(active,k)) for _ in range(100))
            for group in itertools.chain(consecutive,random_groups):
                term=rank_two_update(group,slices,subspaces,rng)
                if term is not None:
                    chosen.append(term)
                    did_work=True
                    break
            if not did_work:
                break
    cost= len(chosen)+sum((len(x[0])+1)//2 for x in subspaces)
    assert cost==base_cost-sum(t[-1].bit_count()-1 for t in chosen)
    return slices,chosen,cost,base_cost

def mobius(values):
    data=np.array(values,copy=True)
    for axis in range((len(data)-1).bit_length()):
        idx=np.arange(1<<axis,len(data))
        dst=idx[((idx>>axis)&1)!=0]
        data[dst]^=data[dst^(1<<axis)]
    return data

def packed(sequence):
    p=np.packbits(np.asarray(sequence,dtype=np.uint8),bitorder="little")
    return int.from_bytes(p.tobytes(),"little")

def factor_columns(columns):
    pivots,null=eliminate(columns)
    # Each pivot, by construction, is an independent reduced column of A.
    rank=list(pivots.values())
    pivot_index={v:i for i,(v,_) in enumerate(rank)}
    symbolic={k:(v,1<<pivot_index[v]) for k,(v,_) in pivots.items()}
    highs=[0]*len(rank)
    for c,col in enumerate(columns):
        missing,expr=reduce(symbolic,col)
        assert missing==0
        for i in bits(expr):highs[i]|=1<<c
    return [(r,h) for (r,_),h in zip(rank,highs)]

def complete_columns(columns, masks):
    independent=[]
    completed=[]
    for col,mask in zip(columns,masks):
        projected=[value&mask for value in independent]
        rem,expr=reduce(eliminate(projected)[0],col&mask)
        if rem:
            value=col&mask
            independent.append(value)
        else:
            value=linear_combo(independent,expr)
        assert (value^col)&mask==0
        completed.append(value)
    return completed

def partition_bits(mask):
    low=list(bits(mask))
    high=[i for i in range(11) if i not in low]
    lows=sorted(sum(1<<q for j,q in enumerate(low) if m>>j&1) for m in range(1<<len(low)))
    highs=sorted(sum(1<<q for j,q in enumerate(high) if m>>j&1) for m in range(1<<len(high)))
    lows=[m for m in lows if m<N]
    highs=[m for m in highs if m<N]
    return lows[1:],highs[1:]

def matrix_from_values(delta, lm, hm):
    coded=delta.astype(np.uint64).copy()
    coded^=(coded&64)<<1
    words=np.zeros(2048,np.uint64)
    for col in range(J):words[:N]^=coded[:,col]<<(8*col)
    anf=mobius(words)
    coeff=np.zeros((len(lm),len(hm)),dtype=np.uint64)
    care=(np.asarray(lm)[:,None]|np.asarray(hm)[None,:])<N
    masks=[packed(care[:,i]) for i in range(len(hm))]
    assert all(a|b==a for a,b in zip(masks,masks[1:]))
    for i,l in enumerate(lm):
        for j,h in enumerate(hm):
            if care[i,j]:coeff[i,j]=anf[l|h]
    outputs=[]
    for o in range(8*J):
        bit=((coeff>>o)&1).astype(np.uint8)
        cols=[packed(bit[:,j]) for j in range(len(hm))]
        cols=complete_columns(cols,masks)
        outputs.append([sum(((col>>i)&1)<<h for h,col in enumerate(cols))
                        for i in range(len(lm))])
    return outputs

def terms_from_groups(slices, lm, hm):
    for o,rows in enumerate(slices):
        columns=[sum(((row>>h)&1)<<l for l,row in enumerate(rows)) for h in range(len(hm))]
        factors=factor_columns(columns)
        for i in range(0,len(factors),2):
            a,h0=factors[i]
            b,h1=factors[i+1] if i+1<len(factors) else (0,0)
            yield (a,h1,b,h0,1<<o)
    
def synthesize(delta,lm,hm,terms):
    lines=[]
    for q in range(11):lines.append(f'APPEND_TO_REGISTER q{q} r0')
    lines.append('REGISTER r0 "selection"')
    for j in range(J):
        for b in range(8):lines.append(f'APPEND_TO_REGISTER q{11+8*j+b} r{j+1}')
        lines.append(f'REGISTER r{j+1} "word_{j}"')
        lines.append(f'CX q{17+8*j} q{18+8*j}')
    cursor=11+8*J
    nodes=[]
    wires={1<<j:j for j in range(11)}
    for subset in (lm,hm):
        for mask in subset:
            if mask in wires: continue
            unit=mask&-mask
            a,b=wires[unit],wires[mask^unit]
            wires[mask]=cursor
            nodes.append((a,b,cursor))
            lines.append(f'CCX q{a} q{b} q{cursor}')
            cursor+=1
    ca,cb=cursor,cursor+1
    assert cb<128
    x=np.arange(N)
    truth={m:packed((x&m)==m) for m in lm+hm}
    wanted=delta.astype(np.uint64).copy()
    wanted^=(wanted&64)<<1
    residual=[packed((wanted[:,j]>>i)&1) for j in range(J) for i in range(8)]
    def form(l,h,wire):
        support=[lm[i] for i in bits(l)]+[hm[i] for i in bits(h)]
        t=0
        for m in support:t^=truth[m]
        return [f'CX q{wires[m]} q{wire}' for m in support],t
    for la,ha,lb,hb,output in terms:
        a, va=form(la,ha,ca)
        b, vb=form(lb,hb,cb)
        o,*rest=bits(output)
        target=11+o
        fan=[f'CX q{target} q{11+r}' for r in rest]
        lines+=fan+a+b+[f'CCX q{ca} q{cb} q{target}']+b[::-1]+a[::-1]+fan[::-1]
        for r in bits(output): residual[r]^=va&vb
    allow=set(lm+hm)
    for o,target in enumerate(residual):
        d=np.zeros(2048,dtype=np.uint8)
        d[:N]=[(target>>i)&1 for i in range(N)]
        seq=mobius(d)
        if seq[0]:lines.append(f'X q{11+o}')
        for index in np.nonzero(seq[1:N])[0]+1:
            assert index in allow
            lines.append(f'CX q{wires[index]} q{11+o}')
    for a,b,t in reversed(nodes):
        lines.extend((f'HMR q{t} b0',f'CZ q{a} q{b} if b0'))
    for j in range(J):lines.append(f'CX q{17+8*j} q{18+8*j}')
    circuit=km.Circuit('\n'.join(lines)+'\n')
    assert circuit.num_qubits==cb+1
    assert circuit.operation_statistics().num_toffoli_like==len(terms)+len(nodes)
    return circuit,len(nodes)

def prove(circuit,delta):
    one=(1<<N)-1
    state=[0]*circuit.num_qubits
    for i in range(11):state[i]=packed((np.arange(N)>>i)&1)
    address=state[:11]
    initial=[one<<(N*(1+j)) for j in range(8*J)]
    state[11:11+8*J]=initial
    outstanding=0
    measured=0
    for line in str(circuit).splitlines():
        gate,*operands=line.split()
        qs=[int(x[1:]) for x in operands if x.startswith("q")]
        if gate=="X":
            state[qs[0]]^=one
        elif gate=="CX":
            a,b=qs
            state[b]^=state[a]
        elif gate=="CCX":
            a,b,t=qs
            assert (state[a]|state[b])>>N==0
            state[t]^=state[a]&state[b]
        elif gate=="HMR":
            assert not outstanding and operands[-1]=="b0"
            t,=qs
            outstanding=state[t]
            state[t]=0
            measured+=1
        elif gate=="CZ":
            assert operands[-2:]==["if","b0"]
            a,b=qs
            outstanding^=state[a]&state[b]
        else:
            assert gate in {"APPEND_TO_REGISTER","REGISTER"}
    assert state[:11]==address and not any(state[11+8*J:]) and outstanding==0
    for j in range(J):
        for i in range(8):
            o=8*j+i
            assert state[11+o]==initial[o]^packed((delta[:,j]>>i)&1)
    return {"addresses":N,"arbitrary_target_bits":8*J,"HMR_phases_proved":measured,"correct":True}

def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--factorization",type=Path,required=True)
    p.add_argument("--verifiers",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--batches",type=int,nargs="+",default=list(range(13)))
    p.add_argument("--partition",type=int,default=31)
    p.add_argument("--max-group",type=int,default=5)
    p.add_argument("--trials",type=int,default=1)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    full_words=np.load(args.source,allow_pickle=False)[:N].astype(np.uint8)
    assert full_words.shape==(N,75) and sha256(full_words.tobytes()).hexdigest()==PIN
    words=np.pad(full_words,((0,0),(0,3)))
    lm,hm=partition_bits(args.partition)
    receipt=[]
    for k in args.batches:
        prev=words[:,J*(k-1):J*k] if k else np.zeros((N,J),np.uint8)
        delta=words[:,J*k:J*(k+1)]^prev
        matrices=matrix_from_values(delta,lm,hm)
        best=None
        for trial in range(args.trials):
            state,chosen,count,base=share(matrices,random.Random(2026111506+k+trial*1009),args.max_group)
            if best is None or count<best[0]:best=(count,state,chosen,base)
        count,state,chosen,base=best
        terms=chosen+list(terms_from_groups(state,lm,hm))
        assert len(terms)==count
        circuit,bank=synthesize(delta,lm,hm,terms)
        proof=prove(circuit,delta)
        path=args.out/f"angle_k_{k}.kmb"
        circuit.to_file(path,format="kmb")
        record={"batch":k,"file":str(path),"sha256":sha256(path.read_bytes()).hexdigest(),
                "bank_ccx":bank,"independent_core":base,"shared_core":count,
                "shared_by_group":{str(j):sum(1 for t in chosen if t[-1].bit_count()==j)
                                  for j in range(2,args.max_group+1)},
                "ccx":circuit.operation_statistics().num_toffoli_like,
                "Q":circuit.num_qubits,"proof":proof}
        print(json.dumps(record),flush=True)
        receipt.append(record)
    result={"batch":J,"partition_mask":args.partition,"true_word_sha256":PIN,
            "score11_factorization_sha256":sha256(args.factorization.read_bytes()).hexdigest(),
            "circuits":receipt,"ccx_per_pass":sum(row["ccx"] for row in receipt),
            "all_batches_emitted":args.batches==list(range(13))}
    if result["all_batches_emitted"]:
        sys.path.insert(0,str(args.verifiers))
        from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
        family=[km.Circuit.from_file(args.out/f"angle_k_{k}.kmb") for k in range(13)]
        decoded,layout,toffoli=recover_words_from_circuits(family,num_vectors=N,num_angles=75,
                                                          shots_per_address=1,seed=2026111506)
        assert np.array_equal(decoded,full_words) and layout.batch_size==J
        assert toffoli==2*result["ccx_per_pass"]
        result["forward_reverse_native_recovery"]={"PASS":True,"addresses":N,"shots_per_address":1,
                                                   "word_mismatches":0,"observed_toffoli":toffoli}
        result["total_T"]=6662+toffoli
        result["total_Q"]=435
        result["ratio_to_score11_at_fixed_physics"]=435*result["total_T"]/(427*14722)
        result["improves_score11"]=result["ratio_to_score11_at_fixed_physics"]<1
    (args.out/"result.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    main()
