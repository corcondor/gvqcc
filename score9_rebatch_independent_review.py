#!/usr/bin/env python3
"""Independent exact review of the emitted J4 joint family and its rank scope.

Does not import the synthesis/prove helpers, mutate circuits, run the full
numeric verifier, or submit. Only this script and its JSON receipt are owned.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
FAMILY = Path('/workspace/scratch/3815fb5fae06/score9_rebatch_synth/joint')
BASE_NPZ = Path('/workspace/scratch/3815fb5fae06/score8_chem_v27_schur_full/submission.npz')
ACTUAL_WORDS = ROOT/'score8_chem_v27_recovered_words.npy'
DATA_BITS = [8*j+b for j in range(4) for b in range(7)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def packed(values):
    return int(''.join('1' if item else '0' for item in values[::-1]),2)


def parse(circuit):
    out=[]
    for line in str(circuit).splitlines():
        parts=line.split()
        if not parts or parts[0] in {'REGISTER','APPEND_TO_REGISTER'}:
            continue
        qubits=[int(s[1:]) for s in parts[1:] if s.startswith('q')]
        cond=int(parts[-1][1:]) if 'if' in parts else None
        classical=int(parts[-1][1:]) if parts[0]=='HMR' else None
        out.append((parts[0],qubits,cond,classical))
    return out


def prove_affine_target(circuit, instructions, incoming, expected, label):
    """State = address truth function XOR formal arbitrary target-linear form.

    Every nonlinear/phase/measurement operand is checked to be independent of
    the formal target. HMR outcomes are fresh formal variables; coefficients
    must cancel before a classical bit is overwritten and at circuit exit.
    """
    n,J=incoming.shape;one=(1<<n)-1
    address=np.arange(n,dtype=np.uint64)
    constants=[0]*int(circuit.num_qubits)
    linear=[0]*int(circuit.num_qubits)
    selection=list(circuit.register_data['selection'])
    words=[list(circuit.register_data[f'word_{j}']) for j in range(J)]
    public={q.id for reg in [selection]+words for q in reg}
    for b,q in enumerate(selection):constants[q.id]=packed((address>>b)&1)
    for j,reg in enumerate(words):
        for b,q in enumerate(reg):
            constants[q.id]=packed((incoming[:,j]>>b)&1)
            linear[q.id]=1<<(8*j+b)
    phases={};deterministic_phase=0;measurements=0;resets=0;counts=Counter()
    for position,(gate,qs,condition,bit) in enumerate(instructions):
        counts[gate]+=1
        if gate in {'X','CX','CCX','R','HMR'}:
            assert condition is None,(label,position,'unsupported conditioned state mutation')
        if gate=='X':constants[qs[0]]^=one
        elif gate=='CX':
            c,t=qs;constants[t]^=constants[c];linear[t]^=linear[c]
        elif gate=='CCX':
            a,b,t=qs
            assert not linear[a] and not linear[b],(label,position,'target-dependent nonlinear control')
            constants[t]^=constants[a]&constants[b]
        elif gate=='R':
            assert constants[qs[0]]==linear[qs[0]]==0,(label,position,'nonzero reset')
            resets+=1
        elif gate=='HMR':
            q=qs[0]
            assert not linear[q],(label,position,'measurement depends on target')
            assert not phases.get(bit,0),(label,position,'uncancelled overwritten HMR coefficient')
            phases[bit]=constants[q];constants[q]=0;measurements+=1
        elif gate in {'Z','CZ','CCZ','NEG'}:
            phase=one
            for q in qs:
                assert not linear[q],(label,position,'target-dependent phase operand')
                phase &= constants[q]
            if condition is None:deterministic_phase^=phase
            else:
                assert condition in phases,(label,position,'condition is not a tracked measurement')
                phases[condition]^=phase
        else:raise AssertionError((label,position,'unsupported gate',gate))
    assert not deterministic_phase and not any(phases.values()),(label,'residual phase')
    for b,q in enumerate(selection):
        assert constants[q.id]==packed((address>>b)&1) and not linear[q.id],(label,'selection changed')
    for j,reg in enumerate(words):
        for b,q in enumerate(reg):
            assert constants[q.id]==packed((expected[:,j]>>b)&1),(label,'wrong output constant',j,b)
            assert linear[q.id]==1<<(8*j+b),(label,'wrong arbitrary-target linear map',j,b)
    assert all(constants[q]==linear[q]==0 for q in range(len(constants)) if q not in public),(label,'dirty workspace')
    return dict(label=label,status='EXACT_ARBITRARY_TARGET_XOR_AND_ALL_HMR_PHASE_PASS',
                addresses=n,official_addresses_covered=min(n,1220),arbitrary_target_bits=8*J,
                HMR_variables_cancelled=measurements,zero_resets_checked=resets,
                gate_counts=dict(counts),workspace_zero=True,selection_preserved=True)


def low_pivot_rank(values):
    basis={}
    for value in values:
        value=int(value)
        while value:
            p=(value&-value).bit_length()-1
            if p not in basis:
                basis[p]=value;break
            value^=basis[p]
    return len(basis)


def parity32(values):
    v=values.copy()
    for shift in (16,8,4,2,1):v^=v>>shift
    return v&1


def coefficients_independent(delta):
    # Explicit Boolean subset-incidence matrices, not the generator's Mobius.
    converted=delta.astype(np.uint64).copy()
    converted ^= (converted&64)<<1
    values=np.stack([((converted[:,j]>>b)&1) for j in range(4) for b in range(7)],axis=1)
    table=values.reshape(77,16,28).astype(np.uint16)
    h=np.arange(77,dtype=np.uint16);l=np.arange(16,dtype=np.uint16)
    high_subset=((h[:,None]&h[None,:])==h[None,:]).astype(np.uint16)
    low_subset=((l[:,None]&l[None,:])==l[None,:]).astype(np.uint16)
    temp=(high_subset@table.reshape(77,-1)).reshape(77,16,28)&1
    coefficients=(low_subset@temp.transpose(1,0,2).reshape(16,-1)).reshape(16,77,28).transpose(1,0,2)&1
    return coefficients


def prove_complete_rank_list(tensor, candidates):
    """Batch Gaussian elimination on all32767 left contractions.

    Original C++ uses Gray code/high pivots and explicitly builds kernels.
    This uses a binary doubling table, low pivots and verifies each kernel is
    completely covered by the separately supplied deficient-output set.
    """
    contractions=np.zeros((1<<15,76),dtype=np.uint32)
    for b in range(15):
        width=1<<b
        contractions[width:2*width]=contractions[:width]^tensor[b]
    equations=contractions[1:].copy()
    ranks=np.zeros(len(equations),dtype=np.uint8)
    indices=np.arange(len(equations))
    for bit in range(28):
        present=(equations&(np.uint32(1)<<np.uint32(bit)))!=0
        exists=present.any(axis=1)
        at=present.argmax(axis=1)
        pivot=equations[indices,at].copy()
        pivot[~exists]=0
        equations ^= np.where(present,pivot[:,None],np.uint32(0))
        ranks+=exists
    assert not equations.any()
    kernel_dimensions=28-ranks
    assert int(kernel_dimensions.max())<=20
    coverage=np.zeros(len(ranks),dtype=np.uint32)
    for mask in candidates:
        valid=(parity32(contractions[1:]&np.uint32(mask))==0).all(axis=1)
        coverage+=valid
    assert np.array_equal(coverage,np.left_shift(np.uint32(1),kernel_dimensions)), 'incomplete/extraneous kernel union'
    # Each listed nonzero output must actually be rank-deficient.
    output_ranks={}
    for mask in candidates:
        coefficients=parity32(tensor&np.uint32(mask))
        rows=[packed(row) for row in coefficients]
        r=low_pivot_rank(rows);output_ranks[int(mask)]=r
        if mask:assert r<15
    return dict(nonzero_left_vectors_checked=32767,
                rank_deficient_outputs_including_zero=len(candidates),
                nontrivial_left_kernels=int(np.count_nonzero(kernel_dimensions)),
                maximum_kernel_dimension=int(kernel_dimensions.max()),
                kernel_coverage_complete=True,output_ranks=output_ranks)


def joint_identity_review(coefficients,basis,expected_core):
    columns=[]
    for mask in basis:
        z=np.zeros((77,16),dtype=np.uint8)
        for bit in range(28):
            if mask>>bit&1:z^=coefficients[:,:,bit].astype(np.uint8)
        columns.append([packed(z[h,:])&~1 for h in range(77)])
    # The high constant column is pure-low and excluded from cross rank.
    for column in columns:column[0]=0
    ranks=[low_pivot_rank(c) for c in columns]
    full=[i for i,r in enumerate(ranks) if r==15]
    checks=[]
    for a,b in zip(full[::2],full[1::2]):
        ca,cb=columns[a],columns[b]
        ha=sum(((ca[h]>>1)&1)<<h for h in range(77))
        hb=sum(((cb[h]>>2)&1)<<h for h in range(77))
        shared=[(((ha>>h)&1)<<1)^(((hb>>h)&1)<<2) for h in range(77)]
        ra=low_pivot_rank([x^s for x,s in zip(ca,shared)])
        rb=low_pivot_rank([x^s for x,s in zip(cb,shared)])
        assert ra<=14 and rb<=14
        checks.append(dict(outputs=[a,b],before_ranks=[15,15],after_ranks=[ra,rb],
                           original_pair_cost=16,joint_pair_cost=1+(ra+1)//2+(rb+1)//2))
    original=sum((r+1)//2 for r in ranks)
    expected=original-len(checks)
    assert expected==expected_core,(expected,expected_core)
    return dict(original_core=original,joint_core=expected,pairs=len(checks),checks=checks)


def main():
    sys.path.append('/workspace/scratch/7f542e06b7cf/kickmix_venv/lib/python3.12/site-packages')
    import kickmix as km
    started=time.monotonic()
    metadata=json.loads((FAMILY/'result.json').read_text())
    accepted=json.loads((ROOT/'score8_scorecard.json').read_text())
    words=np.load(ACTUAL_WORDS,allow_pickle=False).astype(np.uint64)
    extended=np.load(FAMILY/'source_words_1232.npy',allow_pickle=False).astype(np.uint64)
    assert words.shape==(1220,75) and extended.shape==(1232,75)
    assert np.array_equal(words,extended[:1220])
    assert sha(FAMILY/'submission.npz')==sha(BASE_NPZ)==metadata['factorization_sha256']
    padded=np.pad(extended,((0,0),(0,1)))
    reference_layout=None;rows=[];loader_total=0;shared_savings=0
    # Exact four-variable identity: mixed product differs only by pure-bank terms.
    identity_cases=[]
    for assignment in range(16):
        l1,l2,a,b=[(assignment>>i)&1 for i in range(4)]
        mixed=(l1^b)&(l2^a)
        cross=(l1&a)^(l2&b)
        assert mixed^(l1&l2)^(a&b)==cross
        identity_cases.append([assignment,mixed,cross])

    for k in range(19):
        path=FAMILY/f'angle_k_{k}.kmb';circuit=km.Circuit.from_file(path)
        source=metadata['rows'][k]
        assert source['batch']==k and sha(path)==source['sha256']
        layout={name:[q.id for q in reg] for name,reg in circuit.register_data.items()}
        if reference_layout is None:reference_layout=layout
        assert layout==reference_layout
        assert layout['selection']==list(range(11))
        assert set(layout)=={'selection','word_0','word_1','word_2','word_3'}
        assert all(layout[f'word_{j}']==list(range(11+8*j,19+8*j)) for j in range(4))
        assert int(circuit.num_qubits)<=128
        previous=padded[:,4*(k-1):4*k] if k else np.zeros((1232,4),np.uint64)
        current=padded[:,4*k:4*(k+1)]
        instructions=parse(circuit)
        checks=[prove_affine_target(circuit,instructions,previous,current,f'{k}/forward'),
                prove_affine_target(circuit,instructions,current,previous,f'{k}/reverse')]
        count=Counter(g for g,_,_,_ in instructions)
        assert not any(cond is not None for g,_,cond,_ in instructions if g in {'CCX','CCZ','CSWAP'})
        ccx=count['CCX']+count['CCZ']+count['CSWAP']
        assert ccx==int(circuit.operation_statistics().num_toffoli_like)==source['ccx']
        coefficients=coefficients_independent(previous^current)
        tensor=np.array([[sum(int(coefficients[h,l,o])<<o for o in range(28))
                          for h in range(1,77)] for l in range(1,16)],dtype=np.uint32)
        lines=(FAMILY/f'k{k:02d}_rank_input.txt').read_text().split()
        assert list(map(int,lines[:3]))==[15,76,28]
        saved=np.array(list(map(int,lines[3:])),dtype=np.uint32).reshape(15,76)
        assert np.array_equal(saved,tensor),'rank input does not match fixed extension'
        candidates=[int(line) for line in (FAMILY/f'k{k:02d}_rank_outputs.txt').read_text().splitlines() if not line.startswith('#')]
        assert len(candidates)==len(set(candidates))
        rank_check=prove_complete_rank_list(tensor,candidates)
        assert rank_check['rank_deficient_outputs_including_zero']==source['rank_deficient_outputs']
        assert rank_check['nontrivial_left_kernels']==source['nontrivial_nullspaces']
        assert rank_check['maximum_kernel_dimension']==source['maximum_kernel_dimension']
        basis=source['output_basis'];assert low_pivot_rank(basis)==28
        # Independently repeat the minimum-weight vector-matroid basis selection.
        choices=[]
        for mask in set(candidates)|{1<<i for i in range(28)}:
            if not mask:continue
            if mask in rank_check['output_ranks']:r=rank_check['output_ranks'][mask]
            else:r=low_pivot_rank([packed(parity32(row&np.uint32(mask))) for row in tensor])
            choices.append(((r+1)//2,mask,r))
        selected=[];best_cost=0
        for cost,mask,_ in sorted(choices):
            if low_pivot_rank(selected+[mask])>len(selected):
                selected.append(mask);best_cost+=cost
            if len(selected)==28:break
        assert len(selected)==28 and best_cost==source['optimal_basis_core_ccx']
        joint=joint_identity_review(coefficients,basis,source['core_products_after_joint'])
        assert joint['original_core']==best_cost
        assert ccx==80+joint['joint_core']
        loader_total+=ccx;shared_savings+=joint['pairs']
        rows.append(dict(batch=k,circuit=pin(path),num_qubits=int(circuit.num_qubits),
                         toffolis=ccx,exact_checks=checks,rank_basis_review=rank_check,
                         independent_minimum_paired_basis_cost=best_cost,joint_identity=joint))
        print(json.dumps(dict(batch=k,exact_phase_and_arbitrary_target=True,ccx=ccx,
                              rank_list_complete=True,joint_pairs=joint['pairs'])),flush=True)

    assert loader_total==5197==metadata['loader_ccx']
    assert shared_savings==237
    total_t=6662+2*loader_total;total_q=387+4*8
    ratio=total_t*total_q/(14722*427)
    cost=accepted['candidate_costs']['dfthcsos']*ratio
    local_score=accepted['local_combined_score']/ratio**(1/3)
    assert total_t==17056 and total_q==419
    assert abs(ratio-metadata['QT_ratio_to_score8'])<1e-14
    assert abs(cost-metadata['chemistry_cost_from_identical_physics'])<1e-6
    result=dict(
        status='INDEPENDENT_EXACT_FAMILY_REVIEW_PASS_COST_WORSE_NOT_ADOPTED',
        review_source=pin(__file__),generator=pin(ROOT/'score9_rebatch_synth.py'),
        rank_search_source=pin(ROOT/'score9_rebatch_synth_rank_basis.cpp'),family_metadata=pin(FAMILY/'result.json'),
        actual_words=pin(ACTUAL_WORDS),fixed_extension=pin(FAMILY/'source_words_1232.npy'),
        candidate_npz=pin(FAMILY/'submission.npz'),accepted_npz=pin(BASE_NPZ),
        same_npz_bytes=True,same_actual1220_angle_words=True,same_physics_metrics_by_identical_inputs=True,
        inherited_metrics=accepted['chemistry_metrics'],
        code_independence='No import of score9_rebatch_synth or outcome_chem_j4_synthesize; own symbolic-target/phase engine, subset-incidence coefficient transform, binary-order left contractions, low-pivot batch elimination and greedy basis check.',
        verification_scope=dict(circuits=19,directions=2,official_addresses=1220,
                                fixed_extension_addresses=1232,official_address_transitions=19*2*1220,
                                all_target_assignments_per_address='all2^32, proved symbolically',
                                HMR_variables_cancelled=sum(c['HMR_variables_cancelled'] for row in rows for c in row['exact_checks']),
                                full_official_numeric_verifier_run=False,submission_performed=False),
        rows=rows,
        joint_identity=dict(formula='(l1+B2)(l2+A1) + l1*l2 + A1*B2 = l1*A1 + l2*B2 over GF(2)',
                            exhaustive_four_bit_cases=identity_cases,
                            application='Subtract the shared cross term from both rank15 slices; each loses a row and has rank at most14. Two7-product residuals plus one shared product use at most15 instead of16. Pure-bank corrections are implemented from the already built complete banks.',
                            total_shared_pairs=shared_savings,total_saved_ccx_per_pass=shared_savings,
                            separate_paired_family_cost=loader_total+shared_savings,joint_family_cost=loader_total),
        rank_optimality_scope={
            'fixed_points':'1232=77*16 addresses, with the chosen values at1220..1231 fixed as part of the tensor. Official physics uses only0..1219; these12 values are otherwise free and were not optimized here.',
            'fixed_model':'15 nonconstant low4 functions times76 nonconstant high7 functions; arbitrary invertible28-dimensional output basis; independently synthesized single-coordinate paired products costing ceil(matrix_rank/2).',
            'complete_enumeration':'Every rank<15 matrix has a nonzero left-null vector. All32767 such vectors were independently checked; candidate kernels cover exactly2^(28-rank) solutions for each contraction.',
            'minimum_basis':'Weighted vector-matroid greedy is exact. All omitted full-rank directions have the same cost8; coordinate units suffice to extend any selected independent set.',
            'not_global':'No lower bound on joint multi-output tensors, alternate1232 extensions, different address splits/banks, alternative angle words, staged data-dependent circuits or general quantum circuits. The237-product joint gain is explicitly outside the independent-output optimum.',
        },
        resources=dict(loader_toffoli_per_pass=loader_total,total_toffoli=total_t,total_qubits=total_q,
                       maximum_angle_qubits=max(row['num_qubits'] for row in rows),QT_ratio_to_score8=ratio,
                       chemistry_cost=cost,local_portfolio_score_if_used=local_score,adopt=False),
        no_blocking_correctness_findings=True,seconds=time.monotonic()-started,
    )
    path=ROOT/'score9_rebatch_independent_review.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],resources=result['resources'],seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
