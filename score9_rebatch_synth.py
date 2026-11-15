#!/usr/bin/env python3
"""Exact J=4 ANGLE synthesis from the circuit-recovered score8 word table.

Unlike the earlier per-output paired builder, this enumerates every deficient
matrix in the output matrix space, finds a minimum-cost output basis, and
supports joint COMM tensor resynthesis. It only claims optimality within the
fixed 4/7 split, arbitrary output-basis + per-coordinate paired-rank class.
All candidate circuits receive an arbitrary-target and all-HMR-phase proof.

Attribution: uses the repository's outcome_chem_j4_synthesize.py helpers;
optional COMM search uses Polytof (ZIB-IOL/polytof, MIT), unmodified executable.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
sys.path.append('/workspace/scratch/7f542e06b7cf/kickmix_venv/lib/python3.12/site-packages')
import kickmix as km
from outcome_chem_j4_synthesize import mobius, packed, factor_columns, prove

REPO = Path(__file__).resolve().parent
DEFAULT_OUT = Path('/workspace/scratch/3815fb5fae06/score9_rebatch_synth')
ACTUAL_HASH = '8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea'
DATA = [8*j+b for j in range(4) for b in range(7)]

def bits(x):
    while x:
        b=x&-x; yield b.bit_length()-1; x^=b

def rank(rows):
    piv={}
    for v in rows:
        while v and v.bit_length()-1 in piv:v^=piv[v.bit_length()-1]
        if v:piv[v.bit_length()-1]=v
    return len(piv)

def xor_rows(mask, rows):
    result=[0]*len(rows[0])
    for i in bits(mask):result=[a^b for a,b in zip(result,rows[i])]
    return result

def coefficients(delta):
    converted=delta.astype(np.uint64).copy()
    converted ^= (converted&64)<<1
    anf=converted.reshape(77,16,4).copy()
    for h in range(77):anf[h]=mobius(anf[h])
    return mobius(anf)

def output_basis(anf, out, k):
    matrices=[]
    for wire in DATA:
        j,b=divmod(wire,8)
        matrices.append([packed((anf[1:,l,j]>>b)&1) for l in range(1,16)])
    inp=out/f'k{k:02d}_rank_input.txt'; dst=out/f'k{k:02d}_rank_outputs.txt'
    tensor=[[sum(((matrices[c][l]>>h)&1)<<c for c in range(28)) for h in range(76)] for l in range(15)]
    inp.write_text('15 76 28\n'+'\n'.join(' '.join(map(str,row)) for row in tensor)+'\n')
    start=time.monotonic()
    call=subprocess.run([str(out/'rank_basis'),str(inp),str(dst)],capture_output=True,text=True,check=True)
    stats=json.loads(call.stdout)
    deficient=[int(line) for line in dst.read_text().splitlines() if not line.startswith('#')]
    choices=[]
    for mask in sorted(set(deficient)|{1<<i for i in range(28)}):
        if mask:
            r=rank(xor_rows(mask,matrices));choices.append(((r+1)//2,mask.bit_count(),mask,r))
    choices.sort()
    basis=[];piv={};cost=0;ranks=[]
    for c,_,mask,r in choices:
        v=mask
        while v and v.bit_length()-1 in piv:v^=piv[v.bit_length()-1]
        if v:
            piv[v.bit_length()-1]=v;basis.append(mask);cost+=c;ranks.append(r)
            if len(basis)==28:break
    assert len(basis)==28
    original=[rank(m) for m in matrices]
    return basis,dict(**stats,seconds=time.monotonic()-start,original_ranks=original,
                      optimized_ranks=ranks,original_core_ccx=sum((r+1)//2 for r in original),
                      optimal_basis_core_ccx=cost,output_basis=basis,
                      completeness='all nonzero 15-bit left null vectors; union of all output kernels')

def transform_delta(delta,basis):
    converted=delta.astype(np.uint64).copy();converted^=(converted&64)<<1
    flat=sum(converted[:,j]<<(8*j) for j in range(4))
    outputs=np.zeros((1232,28),dtype=np.uint8)
    for i,mask in enumerate(basis):
        for b in bits(mask):outputs[:,i]^=((flat>>DATA[b])&1).astype(np.uint8)
    return converted,outputs

def initial_terms(outputs,joint=False):
    anf=outputs.reshape(77,16,28).copy()
    for h in range(77):anf[h]=mobius(anf[h])
    anf=mobius(anf)
    terms=[]
    column_sets=[[0]+[packed(anf[h,:,o])&~1 for h in range(1,77)] for o in range(28)]
    if joint:
        # For two rank15 slices, share S=l1*A1+l2*B2. Both residual
        # slices have rank14, while S costs one mixed CCX with two-target
        # fanout. This saves one over separate ceil(15/2)+ceil(15/2).
        full=[o for o,c in enumerate(column_sets) if len(factor_columns(c))==15]
        for a,b in zip(full[::2],full[1::2]):
            ha=sum(((column_sets[a][h]>>1)&1)<<h for h in range(77))
            hb=sum(((column_sets[b][h]>>2)&1)<<h for h in range(77))
            for h in range(77):
                shared=(((ha>>h)&1)<<1)^(((hb>>h)&1)<<2)
                column_sets[a][h]^=shared;column_sets[b][h]^=shared
            assert len(factor_columns(column_sets[a]))==14
            assert len(factor_columns(column_sets[b]))==14
            terms.append((1|((hb>>1)<<15),2|((ha>>1)<<15),(1<<a)|(1<<b)))
    for o,columns in enumerate(column_sets):
        pairs=factor_columns(columns)
        for at in range(0,len(pairs),2):
            a,h1=pairs[at]
            if at+1<len(pairs):
                b,h2=pairs[at+1]
                u=(a>>1)|((h2>>1)<<15);v=(b>>1)|((h1>>1)<<15)
            else:u=a>>1;v=(h1>>1)<<15
            terms.append((u,v,1<<o))
    return terms

def tensor_dump(terms,out,k):
    folder=out/'polytof';tensor_path=folder/'data/tensors'/f'{9200+k}.npy'
    pool=folder/'data/cpd/comm'/f'{9200+k}-{len(terms):05d}.npy'
    tensor_path.parent.mkdir(parents=True,exist_ok=True);pool.parent.mkdir(parents=True,exist_ok=True)
    polynomial={}
    for a,b,w in terms:
        for i in bits(a):
            for j in bits(b):
                if i!=j:
                    key=(min(i,j),max(i,j));polynomial[key]=polynomial.get(key,0)^w
    triples=[(i,j,o) for (i,j),w in sorted(polynomial.items()) for o in bits(w)]
    np.save(tensor_path,np.array([(91,91,28)]+triples,dtype=np.int64))
    mask=(1<<64)-1
    row=[part for term in terms for v in term for part in (v&mask,v>>64)]
    np.save(pool,np.array([row],dtype=np.uint64))

def load_pool(path):
    row=np.load(path,allow_pickle=False)[0]
    vectors=[int(row[i])|(int(row[i+1])<<64) for i in range(0,len(row),2)]
    return [(a,b,w) for a,b,w in zip(vectors[::3],vectors[1::3],vectors[2::3]) if a and b and a!=b and w]

def cnot_basis_elimination(basis):
    rows=basis.copy();ops=[]
    for col in range(28):
        pivot=next(i for i in range(col,28) if rows[i]>>col&1)
        if pivot!=col:
            for s,t in [(pivot,col),(col,pivot),(pivot,col)]:rows[t]^=rows[s];ops.append((s,t))
        for i in range(28):
            if i!=col and rows[i]>>col&1:rows[i]^=rows[col];ops.append((col,i))
    assert rows==[1<<i for i in range(28)]
    return ops

def synthesize(delta,basis,terms):
    converted,wanted=transform_delta(delta,basis)
    lines=[]
    for q in range(11):lines.append(f'APPEND_TO_REGISTER q{q} r0')
    lines.append('REGISTER r0 "selection"')
    for j in range(4):
        for b in range(8):lines.append(f'APPEND_TO_REGISTER q{11+8*j+b} r{j+1}')
        lines.append(f'REGISTER r{j+1} "word_{j}"')
        lines.append(f'CX q{17+8*j} q{18+8*j}')
    output_wires=[11+q for q in DATA]
    ops=cnot_basis_elimination(basis)
    for s,t in reversed(ops):lines.append(f'CX q{output_wires[s]} q{output_wires[t]}')
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
    features=[lo[i] for i in range(1,16)]+[hi[i] for i in range(1,77)]
    c1,c2=cursor,cursor+1;lines.extend((f'R q{c1}',f'R q{c2}'))
    low=np.arange(1232)%16;high=np.arange(1232)//16
    truth=np.array([((low&m)==m) for m in range(1,16)]+[((high&m)==m) for m in range(1,77)],dtype=np.uint8)
    residual=wanted.copy()
    def form(mask,wire):return [f'CX q{features[i]} q{wire}' for i in bits(mask)]
    for a,b,w in terms:
        first=form(a,c1);second=form(b,c2)
        va=np.bitwise_xor.reduce(truth[list(bits(a))],axis=0)
        vb=np.bitwise_xor.reduce(truth[list(bits(b))],axis=0)
        out=list(bits(w));target=output_wires[out[0]]
        fan=[f'CX q{target} q{output_wires[o]}' for o in out[1:]]
        lines+=fan+first+second+[f'CCX q{c1} q{c2} q{target}']+list(reversed(second))+list(reversed(first))+list(reversed(fan))
        for o in out:residual[:,o]^=va&vb
    # Exact truth-table residual must be additive across the two banks.
    residual=residual.reshape(77,16,28)
    assert np.array_equal(residual,residual[:,0:1]^residual[0:1,:]^residual[0,0])
    def emit_linear(target,low_values,high_values):
        lc=mobius(low_values);hc=mobius(high_values)
        if int(lc[0])^int(hc[0]):lines.append(f'X q{target}')
        for i in range(1,16):
            if lc[i]:lines.append(f'CX q{lo[i]} q{target}')
        for i in range(1,77):
            if hc[i]:lines.append(f'CX q{hi[i]} q{target}')
    for o in range(28):emit_linear(output_wires[o],residual[0,:,o]^residual[0,0,o],residual[:,0,o])
    for j in range(4):
        tag=(converted[:,j]>>7)&1
        assert np.all(tag.reshape(77,16)==tag[:16])
        emit_linear(18+8*j,tag[:16],np.zeros(77,dtype=np.uint8))
    for a,b,target in reversed(nodes):lines.extend((f'HMR q{target} b0',f'CZ q{a} q{b} if b0'))
    for s,t in ops:lines.append(f'CX q{output_wires[s]} q{output_wires[t]}')
    for j in range(4):lines.append(f'CX q{17+8*j} q{18+8*j}')
    circuit=km.Circuit('\n'.join(lines)+'\n')
    assert circuit.num_qubits<=128
    assert circuit.operation_statistics().num_toffoli_like==80+len(terms)
    return circuit

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=DEFAULT_OUT)
    p.add_argument('--batches',type=int,nargs='+',default=list(range(19)))
    p.add_argument('--polytof-attempts',type=int,default=0)
    p.add_argument('--polytof-path-limit',type=int,default=10000)
    p.add_argument('--joint',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    words=np.load(a.out/'source_words_1232.npy');assert hashlib.sha256(words[:1220].tobytes()).hexdigest()==ACTUAL_HASH
    words=np.pad(words.astype(np.uint64),((0,0),(0,1)));rows=[];start=time.monotonic()
    for k in a.batches:
        delta=words[:,4*k:4*k+4].copy()
        if k:delta^=words[:,4*k-4:4*k]
        basis,row=output_basis(coefficients(delta),a.out,k)
        _,wanted=transform_delta(delta,basis);terms=initial_terms(wanted,a.joint)
        assert len(terms)<=row['optimal_basis_core_ccx']
        row.update(batch=k,core_products_before_joint=len(terms))
        tensor_dump(terms,a.out,k)
        if a.polytof_attempts:
            cmd=['/workspace/scratch/3815fb5fae06/theory_qrom_comm2',str(9200+k),'--continue','--fgs','--plus','--save','--verify','--log','-f',str(a.polytof_path_limit),'-m',str(a.polytof_attempts),'-s','16','-t','1','-p','2000']
            # Driver support differs by version; use a bounded subprocess and
            # retain only completely saved, independently checked pools.
            try:result=subprocess.run(cmd,cwd=a.out/'polytof',capture_output=True,text=True,timeout=55)
            except subprocess.TimeoutExpired as exc:
                result=subprocess.CompletedProcess(cmd,124,(exc.stdout or b'').decode() if isinstance(exc.stdout,bytes) else exc.stdout or '',(exc.stderr or b'').decode() if isinstance(exc.stderr,bytes) else exc.stderr or '')
            (a.out/f'k{k:02d}_polytof.log').write_text(result.stdout+result.stderr)
            row['polytof_returncode']=result.returncode
            pools=list((a.out/'polytof/data/cpd/comm').glob(f'{9200+k}-*.npy'))
            best=min(pools,key=lambda x:int(x.stem.split('-')[1]));terms=load_pool(best)
        circuit=synthesize(delta,basis,terms)
        row.update(core_products_after_joint=len(terms),ccx=int(circuit.operation_statistics().num_toffoli_like),qubits=circuit.num_qubits,proof=prove(circuit,delta))
        dest=a.out/f'angle_k_{k}.kmb';circuit.to_file(dest,format='kmb')
        row['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();rows.append(row)
        (a.out/f'k{k:02d}_result.json').write_text(json.dumps(row,indent=2)+'\n')
        print(json.dumps({key:row[key] for key in ('batch','rank_deficient_outputs','optimal_basis_core_ccx','core_products_after_joint','ccx','qubits')}),flush=True)
    result=dict(status='EXACT_CANDIDATES_BUILT',actual_words_sha256=ACTUAL_HASH,rows=rows,seconds=time.monotonic()-start,joint_shared_products=a.joint,
                optimality_scope='Only independent paired-rank blocks after arbitrary output basis, with fixed native 1232-address extension and fixed4/7 split; joint sharing is outside this optimum.')
    if len(rows)==19:
        sys.path.insert(0,'/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers')
        from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
        circuits=[km.Circuit.from_file(a.out/f'angle_k_{k}.kmb') for k in range(19)]
        recovered,layout,t=recover_words_from_circuits(circuits,num_vectors=1220,num_angles=75,shots_per_address=1,seed=2026111591)
        assert np.array_equal(recovered,words[:1220,:75]) and layout.batch_size==4 and layout.brot==8
        loader=sum(row['ccx'] for row in rows);assert t==2*loader
        factorization=Path('/workspace/scratch/3815fb5fae06/score8_chem_v27_schur_full/submission.npz')
        shutil.copyfile(factorization,a.out/'submission.npz')
        qt_ratio=419*(6662+2*loader)/(427*14722)
        result.update(loader_ccx=loader,total_toffoli=6662+2*loader,total_qubits=419,improves_score8=qt_ratio<1,
                      QT_ratio_to_score8=qt_ratio,chemistry_cost_from_identical_physics=294887961.3668603*qt_ratio,
                      native_recovery=dict(status='PASS',addresses=1220,shots_per_address=1,forward_and_reverse=True,seed=2026111591,word_difference_count=0),
                      factorization_sha256=hashlib.sha256(factorization.read_bytes()).hexdigest(),full_official_verifier_run=False)
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='rows'}),flush=True)

if __name__=='__main__':main()
