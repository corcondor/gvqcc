#!/usr/bin/env python3
"""Bounded single-product pruning using exact inactive-angle truth tables.

Checks a product's full final-output direction, then the entire suffix of
forward batches where its XOR persists. Does not assume a generic XOR loader;
every emitted family must pass both reachable traversals and all HMR phases.
"""
from pathlib import Path
import hashlib,json,time,resource
import numpy as np
import kickmix as km
from chemistry_joint_product_resynthesis import extract,DATA,DATA_INDEX
from chemistry_affine_span_resynthesis import parse_line
from chemistry_reachable_exact_proof import pack,prove_one

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'dqi_inputs/chemistry_4033'
TABLE=SOURCE/'submission_asterios_full.npz'


def inactive_angles(words,edges):
    live=np.zeros((len(words),words.shape[1]+1),dtype=bool);live[:,0]=True
    inactive=np.zeros_like(words,dtype=bool);seen={0}
    for j,(parent,child) in enumerate(edges):
        assert parent in seen and child not in seen;seen.add(int(child))
        active=live[:,parent].copy();inactive[:,j]=~active
        live[:,parent]=active & ((words[:,j]%128)!=64)
        live[:,child]=active & ((words[:,j]%128)!=0)
    return inactive


def basis_state(circuit,words,address_bits):
    state=[0]*circuit.num_qubits;state[:11]=address_bits
    for j in range(5):
        for b in range(8):state[11+8*j+b]=pack((words[:,j]>>b)&1)
    return state


def mutate(state,line,ones):
    gate,q,condition=parse_line(line)
    if condition is not None and gate in {'X','CX','CCX','HMR','R'}:
        raise AssertionError('Unsupported conditioned state mutation')
    if gate=='X':state[q[0]]^=ones
    elif gate=='CX':state[q[1]]^=state[q[0]]
    elif gate=='CCX':state[q[2]]^=state[q[0]]&state[q[1]]
    elif gate in {'HMR','R'}:state[q[0]]=0
    elif gate not in {'','REGISTER','APPEND_TO_REGISTER','CZ'}:raise AssertionError(gate)


def affine_value(form,state,ones):
    value=ones if form&1 else 0;form>>=1;q=0
    while form:
        if form&1:value^=state[q]
        q+=1;form>>=1
    return value


def suffix_directions(ex,circuit):
    diff=[(1<<DATA_INDEX[q]) if q in DATA_INDEX else 0 for q in range(circuit.num_qubits)]
    for line in ex['lines'][ex['last']:]:
        gate,q,condition=parse_line(line)
        if gate=='CX':diff[q[1]]^=diff[q[0]]
        elif gate=='CCX':
            assert not diff[q[0]] and not diff[q[1]],'Nonlinear suffix difference'
        elif gate in {'R','HMR'}:
            assert not diff[q[0]],'Difference reaches discarded scratch'
        elif gate not in {'X','CZ','','REGISTER','APPEND_TO_REGISTER'}:raise AssertionError(gate)
    assert not any(diff[:11]) and not any(diff[51:])
    return diff[11:51]


def main():
    start=time.monotonic();cpu=time.process_time();deadline=start+105
    report_path=OUT/'chemistry_dontcare_v4_results.json'
    if report_path.exists():raise FileExistsError(report_path)
    data=dict(np.load(TABLE,allow_pickle=False));words=data['angle_words'].astype(np.uint64)
    inactive=inactive_angles(words,data['tree_edges']);assert inactive.sum()==1416
    addresses=np.arange(1220,dtype=np.uint64);abits=[pack((addresses>>b)&1) for b in range(11)]
    ones=(1<<1220)-1;zero=np.zeros((1220,5),dtype=np.uint64)
    packed=[[pack(inactive[:,5*k+j]) for j in range(5)] for k in range(15)]
    suffix=[[ones]*5 for _ in range(15)]
    for k in reversed(range(15)):
        suffix[k]=[packed[k][j] & (suffix[k+1][j] if k<14 else ones) for j in range(5)]
    sources=[km.Circuit.from_file(SOURCE/f'angle_k_{k}.kmb') for k in range(15)]
    rows=[];deletions={};deltas={};case_count=0
    for k in range(1,15):
        assert time.monotonic()<deadline,'bounded runtime reached'
        source=sources[k];ex=extract(source);state=basis_state(source,words[:,5*(k-1):5*k],abits)
        for line in ex['lines'][:ex['first']]:mutate(state,line,ones)
        final_directions=suffix_directions(ex,source)
        row=dict(batch=k,products=len(ex['terms']),current_batch_only_hits=0,whole_suffix_hits=0,
                 high_bit_directions=0,zero_support_products=0,min_support=1221,max_support=0,
                 minimum_current_care_violations=None,suffix_inactive_by_slot=[x.bit_count() for x in suffix[k]],
                 source_sha256=hashlib.sha256((SOURCE/f'angle_k_{k}.kmb').read_bytes()).hexdigest())
        candidates=[]
        for n,((a,b,w),pos) in enumerate(zip(ex['terms'],ex['positions'])):
            p=affine_value(a,state,ones)&affine_value(b,state,ones)
            support=p.bit_count();row['min_support']=min(row['min_support'],support);row['max_support']=max(row['max_support'],support)
            if not p:row['zero_support_products']+=1
            output_mask=sum(1<<j for j,f in enumerate(final_directions) if (f&w).bit_count()&1)
            bits=[j for j in range(40) if output_mask>>j&1]
            if any(j%8>=6 for j in bits):row['high_bit_directions']+=1
            allowed=ones;allowed_suffix=ones;violations=0
            for j in bits:
                local=packed[k][j//8] if j%8<6 else 0
                tail=suffix[k][j//8] if j%8<6 else 0
                allowed&=local;allowed_suffix&=tail
                violations+=(p & (ones^local)).bit_count()
            row['minimum_current_care_violations']=violations if row['minimum_current_care_violations'] is None else min(row['minimum_current_care_violations'],violations)
            local_ok=not(p & (ones^allowed));suffix_ok=not(p & (ones^allowed_suffix))
            row['current_batch_only_hits']+=int(local_ok);row['whole_suffix_hits']+=int(suffix_ok)
            if suffix_ok:candidates.append(dict(product_index=n,line_position=pos,support=support,output_mask=output_mask,truth=p))
            case_count+=1220
        if candidates:
            deletions[k]=[c['line_position'] for c in candidates]
            deltas[k]=candidates
        rows.append(row);print(json.dumps(row),flush=True)
    total=sum(r['products'] for r in rows);hits=sum(r['whole_suffix_hits'] for r in rows)
    result=dict(status='SINGLE_PRODUCT_CANDIDATES' if hits else 'NO_SINGLE_PRODUCT_DC_PRUNING',
        scope='Drop one existing normalized product, without changing other products, iff its full output XOR touches only inactive low bits in every affected forward batch; no pair/global synthesis search.',
        processed_batches=list(range(1,15)),batch0_excluded=True,products_checked=total,address_product_cases=case_count,
        current_batch_only_hits=sum(r['current_batch_only_hits'] for r in rows),whole_suffix_hits=hits,
        inactive_entries=1416,independent_low_bit_dontcares=8496,loaders=rows,
        source_npz_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest(),
        generator_sha256=hashlib.sha256((OUT/'chemistry_gauge_v4_dontcare_check.py').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_files_modified=False,full_official_shots_run=False,score_improvement_claimed=False)
    if hits:
        candidates=[];changed=words.copy();running=[0]*40
        for k,source in enumerate(sources):
            lines=str(source).splitlines();omit=set(deletions.get(k,[]))
            candidate=km.Circuit('\n'.join(line for pos,line in enumerate(lines) if pos not in omit)+'\n') if omit else source
            for c in deltas.get(k,[]):
                for j in range(40):
                    if c['output_mask']>>j&1:running[j]^=c['truth']
            for j,t in enumerate(running):
                if t:
                    bit_values=np.array([(t>>a)&1 for a in range(1220)],dtype=np.uint64)
                    changed[:,5*k+j//8]^=bit_values<<(j%8)
            candidates.append(candidate)
        difference=words^changed
        assert not np.any(difference & 192)
        assert not np.any(difference[~inactive])
        assert np.array_equal(inactive,inactive_angles(changed,data['tree_edges']))
        checks=[]
        for k,candidate in enumerate(candidates):
            previous=changed[:,5*(k-1):5*k] if k else zero;current=changed[:,5*k:5*(k+1)]
            for direction,x,y in [('forward',previous,current),('reverse',current,previous)]:checks.append(prove_one(candidate,x,y,abits,f'pruned{k}/{direction}'))
            assert candidate.num_qubits<=128
        outdir=OUT/'chemistry_dontcare_v4_candidate';assert not outdir.exists();outdir.mkdir()
        hashes={}
        for k,candidate in enumerate(candidates):
            path=outdir/f'angle_k_{k}.kmb';candidate.to_file(path,format='kmb');hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        data['angle_words']=changed.astype(data['angle_words'].dtype);np.savez_compressed(outdir/'submission.npz',**data)
        result.update(status='EXACT_DONTCARE_PRODUCT_CANDIDATE_PASS',checks=checks,circuit_hashes=hashes,
            loader_toffoli_per_pass=sum(c.operation_statistics().num_toffoli_like for c in candidates),
            ccx_removed_per_pass=hits,changed_words=int(np.count_nonzero(changed!=words)),
            candidate_npz_sha256=hashlib.sha256((outdir/'submission.npz').read_bytes()).hexdigest())
    result.update(elapsed_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    report_path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'loaders','checks','circuit_hashes'}},indent=2))


if __name__=='__main__':main()
