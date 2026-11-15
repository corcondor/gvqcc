#!/usr/bin/env python3
"""Screen actual final-batch product deletions against exact tensor residuals.

The deleted gate's entire final-output direction is applied to angle_words.
For the last five Givens angles, only a small orbital-coordinate subset moves;
the exact H2 residual update uses its symmetric pair-coordinate block.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import argparse,hashlib,json,time,sys
sys.path.append('/workspace/scratch/7f542e06b7cf/kickmix_venv/lib/python3.12/site-packages')
import numpy as np
import kickmix as km
from scipy.optimize import linear_sum_assignment
from score_chemistry_fast_model import FastFixedAngles
from score8_chem_shared_features import SOURCE,TABLE
from chemistry_joint_product_resynthesis import extract
from chemistry_dontcare_v4_prune import basis_state,mutate,affine_value,suffix_directions
from chemistry_reachable_exact_proof import pack,prove_one
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--keep',type=int,default=6);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();data=dict(np.load(TABLE));words=data['angle_words'].astype(np.uint64)
    model=FastFixedAngles(data);r,b,c=data['W'].shape;N=model.N;w=data['W'];ii=data['H2_I'];d=ii-w.sum(1)
    rows,cols,scale=model.rows,model.cols,model.scale;D=len(rows)
    u0=reconstruct_u_vectors(words/128.,data['tree_edges']);u0/=np.linalg.norm(u0,axis=1)[:,None]
    V=model.V.reshape(r,b,D);X=np.einsum('rbc,rbd->rcd',w,V,optimize=True).reshape(r*c,D)
    target=model.ref['tei'][rows[:,None],cols[:,None],rows[None,:],cols[None,:]].copy()
    ss=model.S[rows,cols];ident=(rows==cols).astype(float)
    target+=.5*(np.outer(ss,ident)+np.outer(ident,ss));target*=scale[:,None]*scale[None,:]
    residual=X.T@X-target;del target
    orbitals=np.unique(data['tree_edges'][70:].ravel());subset=np.flatnonzero(np.isin(rows,orbitals)|np.isin(cols,orbitals))
    other=np.setdiff1d(np.arange(D),subset);A=X[:,other];B=X[:,subset];AA=A@A.T
    outside_projection=A@residual[np.ix_(other,subset)];Rss=residual[np.ix_(subset,subset)]
    vs=V.reshape(r*b,D)[:,subset];sr,sc,sw=rows[subset],cols[subset],scale[subset]
    coefficients=np.einsum('rbc,rc->rb',w,d).ravel();hbase=model.hbase
    lam_h2=.25*np.sum((np.abs(w).sum(1)+np.abs(ii))**2)
    offsetgap=model.gap_const+.5*np.sum(d*d)
    source=km.Circuit.from_file(SOURCE/'angle_k_14.kmb');ex=extract(source)
    abits=[pack((np.arange(1220,dtype=np.uint64)>>bit)&1) for bit in range(11)];ones=(1<<1220)-1
    state=basis_state(source,words[:,65:70],abits)
    for line in ex['lines'][:ex['first']]:mutate(state,line,ones)
    final=suffix_directions(ex,source);records=[]
    def make(row):
        changed=words.copy();hit=np.array(row['addresses'],dtype=int)
        changed[hit,70:75]^=np.array(row['slot_xor'],dtype=np.uint64)
        return changed
    for index,((a,bb,out),position) in enumerate(zip(ex['terms'],ex['positions'])):
        truth=affine_value(a,state,ones)&affine_value(bb,state,ones)
        outputmask=sum(1<<j for j,f in enumerate(final) if (f&out).bit_count()%2)
        addresses=[i for i in range(1220) if truth>>i&1]
        slots=[(outputmask>>(8*j))&255 for j in range(5)]
        row=dict(index=index,line_position=position,addresses=addresses,support=len(addresses),slot_xor=slots)
        changed=make(row);u=reconstruct_u_vectors(changed/128.,data['tree_edges']);u/=np.linalg.norm(u,axis=1)[:,None]
        assert np.max(abs(u[:,np.setdiff1d(np.arange(N),orbitals)]-u0[:,np.setdiff1d(np.arange(N),orbitals)]))<1e-12
        dv=(u[N:,sr]*u[N:,sc])*sw-vs
        dx=np.einsum('rbc,rbd->rcd',w,dv.reshape(r,b,len(subset)),optimize=True).reshape(r*c,len(subset))
        dss=B.T@dx+dx.T@B+dx.T@dx
        cross_linear=4*np.sum(outside_projection*dx);cross_square=2*np.sum((AA@dx)*dx)
        square=model.e20+cross_linear+cross_square+2*np.sum(Rss*dss)+np.sum(dss*dss)
        hp=hbase-np.einsum('a,ap,aq->pq',coefficients,u[N:],u[N:],optimize=True)
        ev,vec=np.linalg.eigh(hp);rr,cc=linear_sum_assignment(-np.abs(u[:N]@vec));match=np.empty(N,int);match[rr]=cc
        qrec=np.einsum('j,jp,jq->pq',ev[match],u[:N],u[:N],optimize=True)
        e1=float(np.linalg.norm(qrec-hp));lh1=float(np.abs(ev).sum());lam=lh1+lam_h2;gap=offsetgap+lh1-ev.sum()
        eff=float(np.sqrt(gap*(2*lam-gap))) if 0<gap<2*lam else None
        row.update(error1=e1,error2=float(np.sqrt(max(square,0))),Lambda=float(lam),E_gap=float(gap),lambda_eff=eff,
            changed_words=int(np.count_nonzero(changed!=words)),tag_preserved=bool(np.array_equal(((changed>>6)^(changed>>7))&1,((words>>6)^(words>>7))&1)))
        assert row['tag_preserved'];records.append(row)
        if index%10==0:print(json.dumps(dict(done=index+1,total=len(ex['terms']),best_error2=min(v['error2'] for v in records),seconds=time.monotonic()-started)),flush=True)
    records.sort(key=lambda x:x['error2']);selected=[]
    for idx,row in enumerate(records[:args.keep]):
        changed=make(row);candidate=dict(data);candidate['angle_words']=changed.astype(data['angle_words'].dtype)
        u=reconstruct_u_vectors(changed/128.,data['tree_edges']);u/=np.linalg.norm(u,axis=1)[:,None];candidate['U']=u[N:].reshape(r,b,N)
        path=args.out/f'candidate_{idx:02d}.npz';np.savez_compressed(path,**candidate)
        circuit=km.Circuit('\n'.join(line for i,line in enumerate(ex['lines']) if i!=row['line_position'])+'\n')
        proof=[prove_one(circuit,x,y,abits,f'deleted{row["index"]}/{direction}') for direction,x,y in [('forward',changed[:,65:70],changed[:,70:75]),('reverse',changed[:,70:75],changed[:,65:70])]]
        cp=args.out/f'candidate_{idx:02d}_angle_k_14.kmb';circuit.to_file(cp,format='kmb')
        record=dict(row,candidate=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),circuit=str(cp),
            circuit_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),circuit_ccx=int(circuit.operation_statistics().num_toffoli_like),proof=proof)
        if idx<2:
            official=evaluate_dfthc_angle_words(changed,w,d,model.S,model.beta,model.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
            assert abs(official['error_2']-record['error2'])<1e-8
            assert abs(official['error_1']-record['error1'])<1e-8
            record['official_numeric_metrics']=official
        selected.append(record);print(json.dumps({k:v for k,v in record.items() if k not in {'addresses','proof'}}),flush=True)
    report=dict(status='FINAL_BATCH_ACTUAL_CCX_DELETION_SCREENED',source_table=str(TABLE),source_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest(),
        tested=len(records),affected_orbitals=orbitals.tolist(),affected_pair_coordinates=len(subset),best=selected,
        rankings=[{k:v for k,v in row.items() if k!='addresses'} for row in records],
        baseline_loader_ccx_per_pass=4033,candidate_loader_ccx_per_pass=4032,candidate_T=14726,candidate_Q=427,
        lambda_break_even=46.90647039844889*14728/14726,seconds=time.monotonic()-started,full_circuit_verified=False)
    (args.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'best','rankings'}}),flush=True)

if __name__=='__main__':main()
