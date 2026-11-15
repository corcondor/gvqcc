#!/usr/bin/env python3
"""Materialize a shared-feature angle change and prove both circuit directions."""
from pathlib import Path
import argparse,hashlib,json,shutil,time
import numpy as np
import kickmix as km
from score8_chem_shared_features import SOURCE,TABLE,expression,basis
from chemistry_joint_product_resynthesis import extract,DATA,DATA_INDEX,synthesize,reduce_terms
from chemistry_dontcare_v4_prune import suffix_directions
from chemistry_reachable_exact_proof import pack,prove_one

def target_exit(ex,circuit,slot_bit):
    final=suffix_directions(ex,circuit)
    vectors=[]
    for q in DATA:
        out=sum(1<<j for j,f in enumerate(final) if f>>DATA_INDEX[q]&1)
        vectors.append((out,1<<DATA_INDEX[q]))
    result=expression(1<<slot_bit,basis(vectors));assert result is not None
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--proposal',type=Path,required=True);p.add_argument('--index',type=int,default=0)
    p.add_argument('--mode',choices=['prefix','product'],default='prefix');p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();start=time.monotonic();a.out.mkdir(parents=True,exist_ok=False)
    records=json.loads(a.proposal.read_text());record=records['candidates'][a.index];proposal=record.get('proposal',record)
    data=dict(np.load(a.candidate));words=data['angle_words'].astype(np.uint64)
    old=dict(np.load(TABLE))['angle_words'].astype(np.uint64);k=proposal['batch'];angle=proposal['angle'];slot_bit=8*(angle%5)
    metadata=json.loads(Path(__file__).with_name('score8_chem_shared_features.json').read_text())
    changes=np.argwhere(words!=old);expected=old.copy()
    if a.mode=='prefix':
        for h in proposal['groups']:expected[h*16:min(h*16+16,1220),angle]^=1
    else:expected[proposal['addresses'],angle]^=1
    assert np.array_equal(expected,words)
    abits=[pack((np.arange(1220,dtype=np.uint64)>>b)&1) for b in range(11)]
    zero=np.zeros((1220,5),dtype=np.uint64);checks=[];rows=[]
    for batch in range(15):
        source=km.Circuit.from_file(SOURCE/f'angle_k_{batch}.kmb');candidate=source;added_cx=0
        if batch in (k,k+1,3,4):
            ex=extract(source);wanted=target_exit(ex,source,slot_bit)
            if a.mode=='prefix':
                meta=metadata['live'][str(batch)];base={int(p):(int(v,16),int(r,16)) for p,(v,r) in meta['basis'].items()}
                code=[]
                modifications=[]
                # Preserve the already-accepted score2/current baseline edit.
                if batch in (3,4):modifications.append(([0,76],32))
                if batch in (k,k+1):modifications.append((proposal['groups'],slot_bit))
                for groups,bit in modifications:
                    control=expression(sum(1<<h for h in groups),base);assert control is not None
                    wanted=target_exit(ex,source,bit)
                    for q in range(source.num_qubits+1):
                        if not(control>>q&1):continue
                        for t in DATA:
                            if wanted>>DATA_INDEX[t]&1:
                                code.append(f'X q{t}' if q==source.num_qubits else f'CX q{q} q{t}')
                added_cx=len(code)
                candidate=km.Circuit('\n'.join(ex['lines'][:ex['last']]+code+ex['lines'][ex['last']:])+'\n')
            else:
                if batch in (3,4) and batch not in (k,k+1):
                    raise NotImplementedError('Product-mode builder must preserve the baseline paired patch')
                key='current_expression' if batch==k else 'next_expression'
                expr=int(proposal[key],16);linear=expr&((1<<(1+source.num_qubits))-1)
                products=expr>>(1+source.num_qubits);terms=list(ex['terms'])
                for i,term in enumerate(terms):
                    if products>>i&1:terms[i]=(term[0],term[1],term[2]^wanted)
                terms,linears=reduce_terms(terms,[(linear,wanted)] if linear else [])
                candidate=km.Circuit(synthesize(ex,terms,linears))
        previous=words[:,5*(batch-1):5*batch] if batch else zero;current=words[:,5*batch:5*(batch+1)]
        for direction,x,y in [('forward',previous,current),('reverse',current,previous)]:
            checks.append(prove_one(candidate,x,y,abits,f'k={batch}/{direction}'))
        path=a.out/f'angle_k_{batch}.kmb';candidate.to_file(path,format='kmb')
        row=dict(batch=batch,qubits=candidate.num_qubits,ccx=int(candidate.operation_statistics().num_toffoli_like),
            source_ccx=int(source.operation_statistics().num_toffoli_like),added_linear_ops=added_cx,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rows.append(row);print(json.dumps(row),flush=True)
    shutil.copyfile(a.candidate,a.out/'submission.npz')
    report=dict(status='EXACT_FORWARD_REVERSE_PHASE_PASS',candidate=str(a.candidate),proposal=proposal,
        changed_words=len(changes),source_table_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest(),
        candidate_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),loaders=rows,
        total_loader_ccx_per_pass=sum(x['ccx'] for x in rows),maximum_loader_qubits=max(x['qubits'] for x in rows),
        proof_cases=36600,checks=checks,official_full_verification_run=False,seconds=time.monotonic()-start)
    (a.out/'proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'checks','loaders'}}),flush=True)

if __name__=='__main__':main()
