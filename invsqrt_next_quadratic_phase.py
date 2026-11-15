#!/usr/bin/env python3
"""Numerical screen of one-AND phase features at zero-scratch cuts.

All candidates cost one additional CCX; clean ancilla q21 is checked on the
complete domain.  A numerical probe is not a valid submitted circuit, and no
KMB is emitted unless a later complete-domain and native validation succeeds.
"""
import json,pathlib,time
import numpy as np
import invsqrt_next_phase_search as M

def main():
    start=time.time();old=pathlib.Path('/workspace/scratch/7f542e06b7cf/invsqrt_structural_work');ds=json.loads((old/'basis.json').read_text())['basis'];pw=np.memmap(old/'basis.u64',dtype='<u8',mode='r',shape=(len(ds),(M.N+63)//64))
    d,b=M.load('base');e,t,ids,theta=M.phase(d,b,np.arange(1,M.N+1));margin=t-abs(e)
    active=np.unique(np.r_[np.arange(0,2048),np.linspace(0,M.N-1,4096,dtype=int),np.argpartition(margin,1024)[:1024],np.argpartition(margin[:100000],512)[:512]])
    B=b[ids].T.copy();BS=B[active];es=e[active];ts=t[active]
    sb=np.asarray(((pw[:,active//64]>>(active%64).astype(np.uint64))&1),dtype=np.uint8)
    candidates=[];seen=set();zero_slots={}
    for line in [7705,8075,8189]:
        ss=[i for i,x in enumerate(ds) if x['kind']=='snapshot' and x['line']==line]
        zero_slots[line]=[ds[i]['qubit'] for i in ss if not pw[i].any()]
        assert 21 in zero_slots[line]
        for ai in range(46):
            for bi in range(ai+1,46):
                if 21 in (ai,bi):continue
                for flip_a in (0,1):
                    for flip_b in (0,1):
                        v=(sb[ss[ai]]^flip_a)&(sb[ss[bi]]^flip_b);key=np.packbits(v).tobytes()
                        if key in seen or not v.any():continue
                        seen.add(key);candidates.append({'line':line,'qubits':[ai,bi],'basis_indices':[ss[ai],ss[bi]],'flips':[flip_a,flip_b],'sample':v})
    results=[];summary={'source_kmx_sha256':'69872bf5557a94e4a7425c9470b7a0451958e18276f2be178b5b0ee27dddb1b1','existing_phase_basis_source':str(M.SOURCE),'full_domain_zero_scratch':zero_slots,'unique_candidates':len(candidates),'active_size':len(active),'experiments':results}
    droporder=list(map(int,np.argsort(abs(theta))))
    for n_drop in (1,2):
        drops=droporder[:n_drop];keep=[i for i in range(len(ids)) if i not in drops];w=1/np.maximum(ts,1);A=np.asarray(BS[:,keep],float)*w[:,None];Q,_=np.linalg.qr(A,mode='reduced');y=(-es+BS[:,drops]@theta[drops])*w;resid=y-Q@(Q.T@y)
        rank=[]
        for c in candidates:
            v=c['sample']*w;v=v-Q@(Q.T@v);norm=v@v
            if norm>1e-10:rank.append((float((v@resid)**2/norm),c))
        rank.sort(key=lambda x:-x[0]);rows=[]
        for score,c in rank[:80]:
            r=M.lp(BS,es,ts,drops,theta,new=c['sample']);rows.append({'candidate':{k:v for k,v in c.items() if k!='sample'},'coarse_result':r,'screen_score':score})
        rows.sort(key=lambda x:x['coarse_result']['margin_scaled'] if x['coarse_result'] else -1e100,reverse=True)
        nrot=34-n_drop;threshold=nrot/np.pi*2**(-((231.2940713535-1)*4/nrot-5.3)/.56)
        print(json.dumps({'drops':drops,'required_margin':threshold,'best_coarse':[{ 'candidate':r['candidate'],'margin':r['coarse_result']['margin_scaled']*M.SCALE} for r in rows[:5]],'elapsed':time.time()-start}),flush=True)
        # The sample LP is an upper bound: do not run expensive full-domain
        # checks on candidates that cannot repay even the extra one CCX.
        positive=[r for r in rows if r['coarse_result']['margin_scaled']*M.SCALE>threshold+1e-15]
        stage={'drops':drops,'nrot':nrot,'extra_ccx':1,'required_margin_turns':threshold,'coarse_rows':rows,'full_rows':[]};results.append(stage)
        for row in positive[:10]:
            c=row['candidate'];vals=[]
            for i,flip in zip(c['basis_indices'],c['flips']):vals.append(np.unpackbits(pw[i].view('u1'),bitorder='little')[:M.N]^flip)
            new=vals[0]&vals[1];r=M.lp(B,e,t,drops,theta,new=new,active=active,iterations=16)
            m=r['margin_scaled']*M.SCALE if r else -1;cost=1+nrot*(.56*np.log2(nrot/(np.pi*m))+5.3)/4 if m>0 else None
            stage['full_rows'].append({'candidate':c,'result':r,'new_rotation_plus_extra_ccx':cost})
            print(json.dumps({'candidate':c,'drops':drops,'full_margin':m,'new_cost':cost}),flush=True)
        summary['elapsed_seconds']=time.time()-start;(M.OUT/'invsqrt_next_quadratic_phase_results.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({'status':'SCREEN_COMPLETE','elapsed_seconds':time.time()-start,'actual_improvement_claimed':False}),flush=True)

if __name__=='__main__':main()
