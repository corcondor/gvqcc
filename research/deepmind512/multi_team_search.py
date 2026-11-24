#!/usr/bin/env python3
"""Eight independent move policies, 512 DISTINCT common-cache basis candidates.

Only source-verified two-bank partial adapter class. Fast cost is exact CX cost
for two 82x82 affine layers (not the entire physical adapter!). Selected full
KMB candidates must be emitted and checked independently.
"""
from __future__ import annotations
import argparse, collections, copy, hashlib, json, os, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
N=82; C=73

def rowops_cost(m):
    rows=m[:]; count=0
    for col in range(N):
        pivot=next((j for j in range(col,N) if (rows[j]>>col)&1),None)
        if pivot is None: raise AssertionError(('rank-deficient',col))
        if pivot != col:
            rows[col]^=rows[pivot]
            rows[pivot]^=rows[col]
            rows[col]^=rows[pivot]
            count+=3
        for j in range(N):
            if j!=col and (rows[j]>>col)&1:
                rows[j]^=rows[col]
                count+=1
    assert rows == [1<<i for i in range(N)]
    return count

def apply(m, move):
    a=m['Aold'];oa=m['Bold'];b=m['Anew'];ob=m['Bnew']
    kind,i,j=move
    assert 0<=i<C and 0<=j<C and i!=j
    if kind=='xor':
        a[i]^=a[j];oa[i]^=oa[j]
        mask=1<<i
        for k in range(N):
            if b[k]&mask: b[k]^=1<<j
    elif kind=='swap':
        a[i],a[j]=a[j],a[i];oa[i],oa[j]=oa[j],oa[i]
        mask=(1<<i)|(1<<j)
        for k in range(N):
            z=b[k]&mask
            if z == 1<<i or z==1<<j: b[k]^=mask
    else: raise ValueError(kind)
    return m

def frame_score(m):
    cx0=rowops_cost(m['Aold'])
    cx1=rowops_cost(m['Anew'])
    lin0=sum((w&2047).bit_count() for w in m['Bold'])
    lin1=sum((w&2047).bit_count() for w in m['Bnew'])
    x0=sum((w>>11)&1 for w in m['Bold']);x1=sum((w>>11)&1 for w in m['Bnew'])
    return (cx0+cx1+lin0+lin1,cx0+lin0,cx1+lin1,x0+x1)

def moves(policy,rng,limit):
    """The eight policies have disjoint proposal generators, not eight AI models."""
    i=rng.randrange(C); j=(i+1+rng.randrange(C-1))%C
    if policy==0:return [('swap',i,j)]
    if policy==1:return [('xor',i,j)]
    if policy==2:return [('xor',i,j),('xor',j,(j+1+rng.randrange(C-1))%C)]
    if policy==3:return [('swap',i,j),('xor',i,j)]
    if policy==4:
        k=(j+1+rng.randrange(C-1))%C
        while k==i:k=(k+1)%C
        return [('swap',i,j),('swap',j,k)]
    if policy==5:
        return [('xor',i,j),('swap',i,j),('xor',i,j)]
    if policy==6:
        m=[]
        for t in range(rng.randint(3,8)):
            x=rng.randrange(C);y=(x+1+rng.randrange(C-1))%C
            m.append(('xor' if rng.random()<.8 else 'swap',x,y))
        return m
    if policy==7:
        m=[]
        for t in range(rng.randint(8,16)):
            x=rng.randrange(C);y=(x+1+rng.randrange(C-1))%C
            m.append(('swap' if rng.random()<.3 else 'xor',x,y))
        return m
    raise AssertionError(policy)

def materialize(baseline,ops):
    m=copy.deepcopy(baseline)
    for op in ops:apply(m,op)
    return m

def signature(m):
    return hashlib.sha256(','.join(map(str,m['Aold'])).encode()).hexdigest()

def search(args):
    base=json.loads((ROOT/'baseline_affine.json').read_text())
    base={k:base[k] for k in ['Aold','Bold','Anew','Bnew']}
    base_score=frame_score(base)
    rng=random.Random(args.seed)
    portfolio=[]
    seen={signature(base)}
    accepted=[]
    progress=[]
    started=time.monotonic()
    # Select the elite archive; allow mutations from inferior parents, so not monotonic.
    elite=[{'ops':[],'cost':base_score[0],'team':-1,'score':base_score,'hash':signature(base)}]
    for episode in range(args.episodes):
        for team in range(8):
            for _ in range(8):
                # Non-monotone archive rather than keep-only-best.
                pool=elite if rng.random()<.67 else accepted[-100:]
                if pool and rng.random()<.56:
                    parent=rng.choice(pool)
                    prev=list(map(tuple,parent['ops']))
                else:prev=[]
                cand=None
                for retry in range(160):
                    op=prev+moves(team,rng,episode)
                    m=materialize(base,op)
                    hs=signature(m)
                    if hs not in seen:
                        cand=(op,m,hs);break
                    # on retries, start from fresh for diversity
                    prev=[]
                if cand is None:raise RuntimeError('Unable to generate unique proposal')
                op,m,hs=cand
                seen.add(hs)
                sc=frame_score(m)
                rec={'id':len(accepted),'episode':episode,'team':team,
                     'ops':[list(a) for a in op],'hash':hs,'basis_rank':73,
                     'basis_invertible_by_generation':True,
                     'affine_cx_cost':sc[0],'matrix_1_cx':sc[1],
                     'matrix_2_cx':sc[2], 'affine_x_cost':sc[3],
                     'delta_affine_cx':sc[0]-base_score[0],
                     'native_partial_KMB_verified':False,'official_score_gain':None}
                accepted.append(rec)
                if sc[0]<base_score[0]+200 and sc[0]<= min(x['cost'] for x in elite)+80:
                    elite.append({'ops':op,'cost':sc[0], 'score':sc, 'team':team,'hash':hs})
                    elite=sorted(elite,key=lambda x:x['cost'])[:64]
        progress.append({'episode':episode,'created':len(accepted),
                         'best_affine_cx':min(x['affine_cx_cost'] for x in accepted)})
    assert len(accepted)==args.episodes*64
    # Sort by actual cost proxy; keep broad candidates for true KMB evaluation.
    best=sorted(accepted,key=lambda x:(x['affine_cx_cost'],len(x['ops'])))
    chosen=best[:args.emit]
    # Explicit negative-control: high-cost random candidates also emitted to verify ranking.
    if args.emit>=6:
        chosen=best[:args.emit-2]+[accepted[len(accepted)//2],accepted[-1]]
    results=[]
    for j,rec in enumerate(chosen):
        out=ROOT/'kmb_candidates'/f'candidate_{rec["id"]:04d}.kmb'
        out.parent.mkdir(exist_ok=True)
        env=dict(os.environ,GVQCC_BASIS_OPS=json.dumps(rec['ops']),GVQCC_ADAPTER_OUT=str(out))
        t=time.monotonic()
        res=subprocess.run([sys.executable,str(ROOT/'build_73d_9t_adapter_evolved.py'),str(ROOT/'public_3357.zip')],env=env,capture_output=True,text=True,timeout=90)
        if res.returncode:
            results.append({'id':rec['id'],'status':'FAIL','tail':(res.stdout+'\n'+res.stderr)[-3500:]})
            continue
        s=json.loads(res.stdout)
        # Only 9 CCX partial and no change in numerical angle table; not a score improvement.
        rec['native_partial_KMB_verified']=True
        rec['verified_real_cx']=s['gates']['CX'];rec['verified_real_t']=s['gates']['CCX']
        results.append({'id':rec['id'],'status':'PASS','kmb':str(out.relative_to(ROOT)),
                        'sha256':s['output_sha256'], 'ccx':s['gates']['CCX'],
                        'cx':s['gates']['CX'],'hmr':s['gates']['HMR'],
                        'phase_zero':s['HMR_phase_coeff_zero_all'],
                        'qubits':s['physical_qubits'],'runtime_s':round(time.monotonic()-t,3)})
    # Keep chosen full-KMB payloads, not all 512 redundant huge KMB files.
    doc={'scope':'Real 73D common-function basis search for k13->k14 adapter; NOT a valid independent ANGLE loader',
      'source_sha256':hashlib.sha256((ROOT/'public_3357.zip').read_bytes()).hexdigest(),
      'baseline_partial_KMB':{'T':9,'CX':2164,'Q':128},'n_proposals':len(accepted),
      'n_distinct_matrices':len(seen)-1,'team_proposal_counts':dict(collections.Counter(x['team'] for x in accepted)),
      'base_affine_CX_proxy':base_score[0],
      'best_affine_CX_proxy':min(x['affine_cx_cost'] for x in accepted),
      'best_proxy_candidate_id':best[0]['id'],
      'real_KMB_emissions':results,
      'best_actual_partial_CX':min([x['cx'] for x in results if x['status']=='PASS'],default=None),
      'best_actual_partial_T':min([x['ccx'] for x in results if x['status']=='PASS'],default=None),
      'score_update':False,
      'limitations':['Only common-73 basis is changed; the quotient rank nine is unchanged.',
                     'All emitted KMBs require dirty retained k13 scratch; they are NOT independent bank14 circuits.',
                     'No complete k13/k14 HMR/output schedule or official KickMix verification.',
                     'Lean source is generated separately; Lean compiler unavailable locally.']}
    (ROOT/'candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in accepted))
    (ROOT/'search_result.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
    (ROOT/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    print(json.dumps({k:v for k,v in doc.items() if k not in ('real_KMB_emissions',)},indent=2,ensure_ascii=False))
    print('verified samples:',results)
    return doc

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--episodes',type=int,default=8,help='episodes*8 teams*8 candidates')
    p.add_argument('--emit',type=int,default=20)
    p.add_argument('--seed',type=int,default=20261124)
    search(p.parse_args())
