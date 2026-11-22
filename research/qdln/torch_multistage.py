"""PyTorch multistage XAG learner with an immutable, bit-exact parent.

Not a whole-KickMix compiler. The caller supplies Boolean post-cache live-wire
states and the parent's factor/control and output-fanout matrices. QDLN learns
additional connections from earlier AND gates to later gates, with a hard
forward pass and a differentiable straight-through estimator.

A student is only a candidate. Never report Toffoli savings without a
separate full-128-wire formal proof, clean ancilla, phase verification, and
native KMB cost accounting.
"""
from __future__ import annotations
import numpy as np
import torch
from torch import nn


def hard_eval(features,a,b,out,hidden_a=None,hidden_b=None):
    """Exact GF(2) evaluation on any batch of Boolean feature vectors."""
    x=np.asarray(features,dtype=np.uint8)
    a=np.asarray(a,dtype=np.uint8)
    b=np.asarray(b,dtype=np.uint8)
    out=np.asarray(out,dtype=np.uint8)
    m=len(a)
    if hidden_a is None:hidden_a=np.zeros((m,m),dtype=np.uint8)
    if hidden_b is None:hidden_b=np.zeros((m,m),dtype=np.uint8)
    h=[]
    for j in range(m):
        left=(x@a[j])%2
        right=(x@b[j])%2
        if j:
            prev=np.stack(h,axis=1)
            left^=(prev@hidden_a[j,:j])%2
            right^=(prev@hidden_b[j,:j])%2
        h.append(left*right)
    return (np.stack(h,axis=1)@out)%2 if h else np.zeros((len(x),out.shape[1]),dtype=np.uint8)


class MultiStageXAG(nn.Module):
    """Trainable causal XOR-AND DAG; the parent is one-level (hidden edges off)."""
    def __init__(self,a,b,out,logit_magnitude=0.65):
        super().__init__()
        init=lambda arr:nn.Parameter(torch.tensor(
            np.where(np.asarray(arr,dtype=np.uint8),logit_magnitude,-logit_magnitude),
            dtype=torch.float32))
        self.a=init(a)
        self.b=init(b)
        self.out=init(out)
        m=len(a)
        self.hidden_a=nn.Parameter(torch.full((m,m),-logit_magnitude))
        self.hidden_b=nn.Parameter(torch.full((m,m),-logit_magnitude))
        self.register_buffer("causal_mask",torch.tril(torch.ones(m,m),diagonal=-1))

    @staticmethod
    def _ste(z):
        p=torch.sigmoid(z)
        return p+((p>=0.5).to(p.dtype)-p).detach()

    def forward(self,features):
        a=self._ste(self.a)
        b=self._ste(self.b)
        out=self._ste(self.out)
        ha=self._ste(self.hidden_a)*self.causal_mask
        hb=self._ste(self.hidden_b)*self.causal_mask
        lo=(1-torch.prod(1-2*features[:,None,:]*a[None,:,:],dim=2))/2
        hi=(1-torch.prod(1-2*features[:,None,:]*b[None,:,:],dim=2))/2
        states=[]
        for j in range(a.shape[0]):
            if j:
                previous=torch.stack(states,dim=1)
                c=(1-torch.prod(1-2*previous*ha[j,:j][None,:],dim=1))/2
                d=(1-torch.prod(1-2*previous*hb[j,:j][None,:],dim=1))/2
                x=lo[:,j]+c-2*lo[:,j]*c
                y=hi[:,j]+d-2*hi[:,j]*d
            else:
                x=lo[:,j];y=hi[:,j]
            states.append(x*y)
        hidden=torch.stack(states,dim=1)
        return (1-torch.prod(1-2*hidden[:,:,None]*out[None,:,:],dim=1))/2

    def hard_weights(self):
        with torch.no_grad():
            pieces=[(w>=0).cpu().numpy().astype(np.uint8) for w in
                    (self.a,self.b,self.out,self.hidden_a,self.hidden_b)]
            causal=self.causal_mask.cpu().numpy().astype(np.uint8)
            pieces[3]*=causal;pieces[4]*=causal
            return pieces


def learn_remove_one(features,parent_a,parent_b,parent_out,*,steps=300,seed=0,
                     drop_index=0,lr=0.065,batch=128):
    """Learn a B-1 gate candidate from exact B-gate native parent matrices.

    This does not silently return an inexact result as a circuit. Keep the
    immutable parent as the incumbent if hard exact equivalence is not reached.
    """
    torch.manual_seed(seed);torch.set_num_threads(2)
    features=np.asarray(features,dtype=np.uint8)
    A=np.asarray(parent_a,dtype=np.uint8)
    B=np.asarray(parent_b,dtype=np.uint8)
    S=np.asarray(parent_out,dtype=np.uint8)
    if not(1<len(A)==len(B)==len(S)):raise ValueError("Need >=2 parent gates")
    if not(0<=drop_index<len(A)):raise ValueError("invalid drop index")
    teacher=hard_eval(features,A,B,S)
    # Baseline is trivially feasible, remains immutable, and is never replaced
    # by an inexact student. This is a proposal search, not a promise of savings.
    keep=[j for j in range(len(A)) if j!=drop_index]
    model=MultiStageXAG(A[keep],B[keep],S[keep])
    adam=torch.optim.Adam(model.parameters(),lr=lr)
    x=torch.from_numpy(features.astype(np.float32))
    y=torch.from_numpy(teacher.astype(np.float32))
    best=int(np.size(teacher));trace=[]
    for step in range(steps):
        rows=torch.randint(len(x),(batch,))
        adam.zero_grad()
        pred=model(x[rows])
        loss=(pred-y[rows]).square().mean()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(),25)
        adam.step()
        if step%40==0 or step==steps-1:
            aa,bb,ss,ha,hb=model.hard_weights()
            out=hard_eval(features,aa,bb,ss,ha,hb)
            errors=int(np.count_nonzero(out^teacher))
            best=min(errors,best)
            trace.append({"step":step,"hard_bit_errors":errors,
                          "hidden_edges":int(ha.sum()+hb.sum())})
            if errors==0:
                # Mandatory additional proof: all formal cached-wire inputs
                # and full native output/phase/cleanup, not provided here.
                return {"reachable_exact":True,"formal_verified":False,
                        "native_KMB_verified":False,"old_AND":len(A),
                        "student_AND":len(keep),"trace":trace,
                        "hard_weights":[a.tolist() for a in (aa,bb,ss,ha,hb)]}
    return {"reachable_exact":False,"formal_verified":False,
            "native_KMB_verified":False,"old_AND":len(A),
            "student_AND":len(keep),"best_bit_errors":best,"trace":trace,
            "incumbent":"original parent unchanged"}
