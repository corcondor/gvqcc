#!/usr/bin/env python3
"""Actual integer +/-1 changes to one-body angle words, with exact assignment."""
from __future__ import annotations
import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from score2_chemistry_discrete_screen import decoder_directions
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--shortlist',type=int,default=300)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    data=dict(np.load(args.source,allow_pickle=False));words=data['angle_words'].astype(np.int64);m=FastFixedAngles(data)
    w=data['W'];offset=data['H2_I']-w.sum(1);c=np.einsum('rbc,rc->rb',w,offset)
    hp=m.hbase-(c.ravel()@m.outer_flat).reshape(m.N,m.N);vals,vec=np.linalg.eigh(hp)
    rr,cc=linear_sum_assignment(-np.abs(m.one@vec));match=np.empty(m.N,dtype=int);match[rr]=cc
    rec=np.einsum('j,jp,jq->pq',vals[match],m.one,m.one,optimize=True);error=rec-hp;e10=float(np.sum(error*error))
    u,tangent,plane=decoder_directions(words[:m.N],data['tree_edges'])
    co=np.cos(np.pi/128.)-1;si=np.sin(np.pi/128.)
    un=(u[:,None,None,:]+co*plane[:,:,None,:]+si*tangent[:,:,None,:]*np.array([-1,1])[None,None,:,None])
    un/=np.linalg.norm(un,axis=3)[:,:,:,None]
    du=un-u[:,None,None,:];dd=np.sum(du*du,axis=3);h=np.einsum('atsj,aj->ats',du,u)
    qn=2*dd+2*h*h+4*h*dd+dd*dd
    de=np.einsum('atsi,ij,atsj->ats',un,error,un,optimize=True)-np.einsum('ai,ij,aj->a',u,error,u)[:,None,None]
    approx=e10+2*vals[match,None,None]*de+vals[match,None,None]**2*qn
    old=words[:m.N,:,None];new=(old+np.array([-1,1])[None,None,:])%256
    tags=(((old>>6)^(old>>7))&1)==(((new>>6)^(new>>7))&1)
    tags[:,:5,:]=False
    order=np.argsort(np.where(tags,approx,np.inf).ravel())[:args.shortlist]
    rows=[]
    for index in order:
        a,t,s=map(int,np.unravel_index(index,approx.shape));one=m.one.copy();one[a]=un[a,t,s]
        rr,cc=linear_sum_assignment(-np.abs(one@vec));newmatch=np.empty(m.N,dtype=int);newmatch[rr]=cc
        newrec=np.einsum('j,jp,jq->pq',vals[newmatch],one,one,optimize=True)
        e1=float(np.linalg.norm(newrec-hp));cost=4 if t//5==14 else 8
        rows.append({'address':a,'angle':t,'old_word':int(words[a,t]),'new_word':int(new[a,t,s]),'step':-1 if s==0 else 1,'error_1':e1,'error1_improvement':float(np.sqrt(e10)-e1),'assignment_changes':int(np.sum(newmatch!=match)),'tag_preserved':True,'provisional_feature_patch_added_task_toffoli':cost,'verified_generic_patch_added_task_toffoli':20 if t//5==14 else 40,'headroom_per_provisional_toffoli':float((np.sqrt(e10)-e1)/cost)})
    byerror=sorted(rows,key=lambda x:x['error_1']);bycost=sorted(rows,key=lambda x:-x['headroom_per_provisional_toffoli'])
    chosen=[];seen=set()
    for row in byerror[:3]+bycost[:3]:
        key=(row['address'],row['angle'],row['step'])
        if key not in seen:seen.add(key);chosen.append(row)
    emitted=[]
    for i,row in enumerate(chosen):
        dd={k:np.array(v,copy=True) for k,v in data.items()};dd['angle_words'][row['address'],row['angle']]=row['new_word']
        path=args.out/f'candidate_{i:02d}.npz';np.savez_compressed(path,**dd)
        item=dict(row);item.update(candidate=str(path),candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),changes=[{'address':row['address'],'column':row['angle'],'old':row['old_word'],'value':row['new_word']}])
        if i<2:
            metrics=evaluate_dfthc_angle_words(dd['angle_words'],w,offset,m.S,m.beta,m.ref,brot=8,tree_edges=dd['tree_edges'],energy_upper=UPPER_ENERGY)
            assert abs(metrics['error_1']-row['error_1'])<1e-9
            item['official_numeric_metrics']=metrics
        emitted.append(item)
    report={'status':'INTEGER_ONEBODY_WORD_SCREEN','source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'baseline_error1':float(np.sqrt(e10)),'screened_moves':int(np.sum(tags)),'exact_shortlist':len(rows),'emitted':emitted,'best_error_moves':byerror[:30],'best_cost_moves':bycost[:30],'two_body_words_and_W_H2I_unchanged':True,'columns_0_to_4_excluded_for_patch_cost':True,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'full_circuit_verified':False}
    (args.out/'onebody.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in {'emitted','best_error_moves','best_cost_moves'}}),flush=True)


if __name__=='__main__':main()
