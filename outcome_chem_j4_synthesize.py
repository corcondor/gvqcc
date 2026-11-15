#!/usr/bin/env python3
"""Exact J=4 loader synthesis, using paired products over complete low/high banks.

The identity (A+H2)(B+H1)+AB+H1*H2=A*H1+B*H2 pairs two
cross-partition products in one CCX. Pure low and pure high Boolean products
are linear in the separately prepared complete monomial banks. This is an
actual candidate builder, not a lower bound or a claim of optimal synthesis.
"""
from __future__ import annotations
import argparse,hashlib,json,math,shutil,sys,time
from pathlib import Path
import numpy as np
import kickmix as km

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'official_sources/Inzainos/verifiers'))
from dfthcsos.scoreinfra.circuits import recover_words_from_circuits


def mobius(a):
    a=np.array(a,copy=True)
    for bit in range((len(a)-1).bit_length()):
        for h in range(len(a)):
            if h>>bit&1:a[h]^=a[h^(1<<bit)]
    return a


def packed(a):
    return sum(int(v)<<i for i,v in enumerate(a))


def values(coeff,n):
    return mobius(np.array([(coeff>>i)&1 for i in range(n)],dtype=np.uint8))


def product(left,right,n):
    return packed(mobius(values(left,n)&values(right,n)))


def factor_columns(columns):
    """Exact GF(2) rank factorization: cross(h,l)=sum A_i(l) B_i(h)."""
    basis={};low=[];high=[]
    for h,v in enumerate(columns):
        expr=0
        while v:
            pivot=v.bit_length()-1
            if pivot in basis:
                val,index=basis[pivot];v^=val;expr^=1<<index
            else:
                index=len(low);low.append(v);high.append(0)
                basis[pivot]=(v,index);expr^=1<<index;break
        for index in range(len(low)):
            if expr>>index&1:high[index]^=1<<h
    for h,wanted in enumerate(columns):
        got=0
        for a,b in zip(low,high):
            if b>>h&1:got^=a
        assert got==wanted
    return list(zip(low,high))


def synthesize(delta):
    assert delta.shape==(1232,4)
    # In these coordinates top-bit XOR bit6 is only a low-address tag.
    transformed=delta.copy();transformed^=(transformed&64)<<1
    anf=transformed.reshape(77,16,4).copy()
    for h in range(77):anf[h]=mobius(anf[h])
    anf=mobius(anf)
    lines=[]
    for q in range(11):lines.append(f'APPEND_TO_REGISTER q{q} r0')
    lines.append('REGISTER r0 "selection"')
    for j in range(4):
        for bit in range(8):lines.append(f'APPEND_TO_REGISTER q{11+8*j+bit} r{j+1}')
        lines.append(f'REGISTER r{j+1} "word_{j}"')
    for j in range(4):lines.append(f'CX q{17+8*j} q{18+8*j}')
    cursor=43;nodes=[]
    def bank(n,offset):
        nonlocal cursor
        wires={1<<b:offset+b for b in range((n-1).bit_length())}
        for mask in range(1,n):
            if mask in wires:continue
            unit=mask&-mask;a=wires[unit];b=wires[mask^unit]
            wires[mask]=cursor;nodes.append((a,b,cursor))
            lines.extend((f'R q{cursor}',f'CCX q{a} q{b} q{cursor}'));cursor+=1
        return wires
    hi=bank(77,4);lo=bank(16,0)
    control1,control2=cursor,cursor+1
    assert control2<128
    lines.extend((f'R q{control1}',f'R q{control2}'))
    def linear(target,low=0,high=0):
        out=[]
        if (low^high)&1:out.append(f'X q{target}')
        for mask,q in lo.items():
            if low>>mask&1:out.append(f'CX q{q} q{target}')
        for mask,q in hi.items():
            if high>>mask&1:out.append(f'CX q{q} q{target}')
        return out
    ranks=[];product_count=0
    for j in range(4):
        for bit in range(8):
            target=11+8*j+bit;coeff=(anf[:,:,j]>>bit)&1
            pure_hi=packed(coeff[:,0]);pure_lo=packed(coeff[0]);pure_lo&=~1
            columns=[0]+[packed(coeff[h])&~1 for h in range(1,77)]
            pairs=factor_columns(columns);ranks.append(len(pairs))
            for at in range(0,len(pairs),2):
                a,h1=pairs[at]
                if at+1<len(pairs):
                    b,h2=pairs[at+1]
                    first=linear(control1,low=a,high=h2)
                    second=linear(control2,low=b,high=h1)
                    pure_lo^=product(a,b,16);pure_hi^=product(h1,h2,77)
                else:
                    first=linear(control1,low=a);second=linear(control2,high=h1)
                lines.extend(first);lines.extend(second)
                lines.append(f'CCX q{control1} q{control2} q{target}')
                lines.extend(reversed(second));lines.extend(reversed(first));product_count+=1
            lines.extend(linear(target,low=pure_lo,high=pure_hi))
    for a,b,target in reversed(nodes):
        lines.extend((f'HMR q{target} b0',f'CZ q{a} q{b} if b0'))
    for j in range(4):lines.append(f'CX q{17+8*j} q{18+8*j}')
    circuit=km.Circuit('\n'.join(lines)+'\n')
    assert circuit.num_qubits<=128
    assert circuit.operation_statistics().num_toffoli_like==80+product_count
    return circuit,dict(cross_ranks=ranks,bank_ccx=80,cross_product_ccx=product_count,ccx=80+product_count,qubits=circuit.num_qubits)


def prove(circuit,delta):
    """All1232addresses, arbitrary32targetbits, everyHMR branch exactly."""
    n=len(delta);one=(1<<n)-1
    state=[0]*circuit.num_qubits
    for q in range(11):state[q]=packed(((np.arange(n)>>q)&1))
    initial_address=state[:11].copy()
    for out in range(32):state[11+out]=one<<(n*(out+1))
    initial_output=state[11:43].copy();phase=0;measurements=0
    for line in str(circuit).splitlines():
        p=line.split();gate=p[0]
        if gate in ('REGISTER','APPEND_TO_REGISTER'):continue
        q=[int(s[1:]) for s in p[1:] if s.startswith('q')]
        if gate=='X':state[q[0]]^=one
        elif gate=='CX':state[q[1]]^=state[q[0]]
        elif gate=='CCX':
            assert state[q[0]]>>n==state[q[1]]>>n==0,'output-dependent control'
            state[q[2]]^=state[q[0]]&state[q[1]]
        elif gate=='R':assert state[q[0]]==0
        elif gate=='HMR':
            assert phase==0
            phase=state[q[0]];state[q[0]]=0;measurements+=1
        elif gate=='CZ':
            assert p[-2:] == ['if','b0']
            phase^=state[q[0]]&state[q[1]]
        else:raise ValueError(gate)
    assert state[:11]==initial_address and not any(state[43:]) and phase==0
    for j in range(4):
        for bit in range(8):assert state[11+8*j+bit]==initial_output[8*j+bit]^packed((delta[:,j]>>bit)&1)
    return dict(status='EXACT_ARBITRARY_TARGET_XOR_AND_PHASE_PASS',addresses=n,output_bits=32,formal_measurement_variables_cancelled=measurements)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-dir',type=Path,default=ROOT/'dqi_inputs/chemistry_4033')
    p.add_argument('--factorization',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    start=time.monotonic();source=[km.Circuit.from_file(a.source_dir/f'angle_k_{k}.kmb') for k in range(15)]
    words,layout,old_t=recover_words_from_circuits(source,num_vectors=1232,num_angles=75,shots_per_address=1,seed=202611151)
    data=dict(np.load(a.factorization,allow_pickle=False))
    assert np.array_equal(words[:1220],data['angle_words'])
    extended=np.pad(words.astype(np.uint64),((0,0),(0,1)))
    a.out.mkdir(parents=True);circuits=[];rows=[]
    for k in range(19):
        delta=extended[:,4*k:4*k+4].copy()
        if k:delta^=extended[:,4*(k-1):4*k]
        circuit,row=synthesize(delta);row.update(k=k,proof=prove(circuit,delta))
        dest=a.out/f'angle_k_{k}.kmb';circuit.to_file(dest,format='kmb')
        row['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();circuits.append(circuit);rows.append(row)
        print(json.dumps({key:row[key] for key in ('k','ccx','qubits')}),flush=True)
    recovered,new_layout,t=recover_words_from_circuits(circuits,num_vectors=1220,num_angles=75,shots_per_address=1,seed=202611152)
    assert np.array_equal(recovered,data['angle_words']) and new_layout.batch_size==4 and new_layout.brot==8
    assert t==2*sum(r['ccx'] for r in rows)
    shutil.copyfile(a.factorization,a.out/'submission.npz')
    total=6662+t;qt=419*total;v27qt=427*14722
    result=dict(status='VALID_EXACT_WORD_J4_FAMILY_NOT_COMPETITIVE' if qt>=v27qt else 'PROMISING_EXACT_WORD_J4_FAMILY',source_factorization=str(a.factorization),source_sha256=hashlib.sha256(a.factorization.read_bytes()).hexdigest(),source_label='original public4033 factorization; not newerpublic4030v27',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),J=4,brot=8,num_circuits=19,word_table_unchanged=True,source_factorization_bytes_preserved=True,source_loader_toffoli_perpass=old_t/2,candidate_loader_toffoli_perpass=t/2,loader_qubits_max=max(r['qubits'] for r in rows),candidate_total_toffoli=total,candidate_total_qubits=419,QT_cost_ratio_to_v27_at_same_lambda=qt/v27qt,native_check=dict(seed=202611152,shots_per_address=1,addresses=1220,forward_and_reverse=True,words_identical=True),full_official_numeric_verifier_run=False,full_default_shots_run=False,rows=rows,seconds=time.monotonic()-start,source_files_modified=False)
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)


if __name__=='__main__':main()
