"""PyTorch on *actual post-HMR* 38-gate restart segment, native warm start.

This is a proposal-only trainer; a hard match must undergo full native
X/CX/CCX/HMR phase and scratch verification before any KMB is updated.
Usage: python research/qdln/post_hmr_pytorch.py /path/to/public_V8.zip
"""
from __future__ import annotations
import argparse
import io
import json
import tempfile
import zipfile
from pathlib import Path
import numpy as np
import torch

from native_warmstart import read_kmb
from post_hmr_screen import initial
from torch_multistage import MultiStageXAG

def unpack(bitset,n):
    return np.unpackbits(
        np.frombuffer(bitset.to_bytes((n+7)//8,'little'),np.uint8),
        bitorder='little')[:n]

def model_features(archive,bank=0,phase=66):
    with zipfile.ZipFile(archive) as z:
        w=np.load(io.BytesIO(z.read('dfthcsos/submission.npz')))['angle_words']
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'angle.kmb'
            p.write_bytes(z.read(f'dfthcsos/angle_k_{bank}.kmb'))
            nq,c,ops=read_kmb(p)
    hr=[i for i,(op,qs) in enumerate(ops) if op==0x50]
    beg=hr[phase-1]+1;end=hr[phase]
    n=2*len(w);full=(1<<n)-1
    x=initial(w,bank,nq)
    for op,qs in ops[:beg]:
        if op==0x31:
            a,b,t=qs;x[t]^=x[a]&x[b]
        elif op==0x21:
            a,b=qs;x[b]^=x[a]
        elif op==0x11:x[qs[0]]^=full
        elif op==0x50:x[qs[0]]=0
        elif op not in (0x10,0x20,0x90,0xa0):
            raise ValueError(f'Unknown prefix op {op:#x}')
    sources=x+[full]
    N=nq+1
    symbolic=[1<<i for i in range(nq)]
    terms=[];products=[]
    for op,qs in ops[beg:end]:
        if op==0x31:
            a,b,t=qs
            terms.append((symbolic[a],symbolic[b]))
            value=x[a]&x[b];products.append(value)
            x[t]^=value
            symbolic[t]^=1<<(N+len(terms)-1)
        elif op==0x21:
            a,b=qs;x[b]^=x[a];symbolic[b]^=symbolic[a]
        elif op==0x11:
            x[qs[0]]^=full
            symbolic[qs[0]]^=1<<nq
        elif op not in (0x10,0x20,0x90,0xa0):
            raise ValueError(f'Unknown in-segment op {op:#x}')
    m=len(terms)
    assert m==38, f'Expected restart segment of 38 ANDs, got {m}'
    A=np.zeros((m,N),np.uint8)
    B=np.zeros((m,N),np.uint8)
    C=np.zeros((m,m),np.uint8)
    D=np.zeros((m,m),np.uint8)
    S=np.zeros((m,nq),np.uint8)
    for j,(aa,bb) in enumerate(terms):
        for i in range(N):
            A[j,i]=(aa>>i)&1;B[j,i]=(bb>>i)&1
        for i in range(j):
            C[j,i]=(aa>>(N+i))&1;D[j,i]=(bb>>(N+i))&1
    for i,y in enumerate(symbolic):
        for j in range(m):
            S[j,i]=(y>>(N+j))&1
    F=np.stack([unpack(v,n) for v in sources],axis=1).astype(np.uint8)
    H=np.stack([unpack(v,n) for v in products],axis=1).astype(np.uint8)
    affected=np.flatnonzero(S.any(axis=0))
    S=S[:,affected]
    target=(H@S)%2
    return F,A,B,C,D,S,target

def eval_hard(F,A,B,C,D,S):
    results=[]
    for j in range(len(A)):
        u=(F@A[j])%2
        v=(F@B[j])%2
        if j:
            prev=np.stack(results,axis=1)
            u^=(prev@C[j,:j])%2
            v^=(prev@D[j,:j])%2
        results.append(u*v)
    return np.stack(results,axis=1)@S%2

def train(archive,steps=80,seed=1,omit=9,logit_temperature=1.0):
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    F,A,B,C,D,S,target=model_features(archive)
    parent=eval_hard(F,A,B,C,D,S)
    assert np.array_equal(parent,target),'Native AND factor recovery failed'
    ids=[j for j in range(38) if j!=omit]
    model=MultiStageXAG(A[ids],B[ids],S[ids])
    with torch.no_grad():
        c=C[np.ix_(ids,ids)]
        d=D[np.ix_(ids,ids)]
        model.hidden_a.copy_(torch.tensor(np.where(c,3.0,-3.0),dtype=torch.float32))
        model.hidden_b.copy_(torch.tensor(np.where(d,3.0,-3.0),dtype=torch.float32))
        for param in model.parameters():
            param.mul_(logit_temperature)
    opt=torch.optim.AdamW(model.parameters(),lr=0.025 if logit_temperature>=.8 else 0.09)
    x=torch.as_tensor(F.astype(np.float32))
    y=torch.as_tensor(target.astype(np.float32))
    best=int(np.size(target));trace=[]
    for step in range(steps):
        rows=torch.randint(F.shape[0],(64,))
        opt.zero_grad()
        loss=(model(x[rows])-y[rows]).square().mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),20)
        opt.step()
        if step%10==0 or step+1==steps:
            aa,bb,ss,cc,dd=model.hard_weights()
            hard=eval_hard(F,aa,bb,cc,dd,ss)
            errors=int(np.count_nonzero(hard^target))
            best=min(best,errors)
            trace.append({'step':step,'hard_mismatch':errors,'soft_loss':float(loss.detach())})
            print('step',step,'hard_mismatch',errors,flush=True)
            if errors==0:break
    return {'status':'HARD_PROPOSAL_ONLY_NOT_KMB','PyTorch':torch.__version__,
            'parent_gate_count':38,'student_gate_count':37,
            'trainable_parameters':sum(p.numel() for p in model.parameters()),
            'input_states':F.shape[0],'source_features':F.shape[1],
            'affected_output_wires':S.shape[1],
            'best_hard_mismatch':best,'exact_legal_output':best==0,
            'native_KMB_verified':False,'official_score_gain':0,
            'parent_incumbent_preserved':True,'trace':trace}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('archive')
    p.add_argument('--steps',type=int,default=80)
    p.add_argument('--temperature',type=float,default=1.0)
    p.add_argument('--out',default='qdln_torch_hmr.json')
    a=p.parse_args()
    receipt=train(a.archive,steps=a.steps,logit_temperature=a.temperature)
    Path(a.out).write_text(json.dumps(receipt,indent=2)+'\n')
