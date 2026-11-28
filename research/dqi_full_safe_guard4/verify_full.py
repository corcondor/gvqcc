#!/usr/bin/env python3
"""Paired native full-circuit test. Never promote a circuit on a failed stress panel."""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np,kickmix as km
from scipy.stats import beta
EXP=np.empty(8190,np.int64);LOG=np.zeros(4096,np.int64);x=1
for i in range(4095):
    EXP[i]=EXP[i+4095]=x;LOG[x]=i;x<<=1
    if x&4096:x^=0x1053
assert x==1 and len(set(EXP[:4095]))==4095
def mul(a,b):return np.where((np.asarray(a)!=0)&(np.asarray(b)!=0),EXP[LOG[a]+LOG[b]],0)
def inv(a):
    assert np.all(a!=0)
    return EXP[4095-LOG[a]]
def bits(v):return (((v[:,:,None]>>np.arange(12))&1).reshape(len(v),-1).T).astype(bool)
def make(weights,mode,seed):
    r=np.random.default_rng(seed);n=len(weights);S=np.zeros((n,70),np.int64)
    M=r.integers(0,4096,(n,4095),dtype=np.int64);p=np.zeros(n,bool)
    if mode=='zero':M.fill(0)
    for i,w in enumerate(weights):
        if not w:continue
        pos=r.choice(4095,int(w),replace=False);xs=EXP[pos]
        if mode=='confluent':
            es=[]
            for j,x in enumerate(xs):
                der=int(x)
                for k,y in enumerate(xs):
                    if k!=j:der=int(mul(der,int(x)^int(y)))
                es.append(int(inv(np.array(der))))
            es=np.array(es,dtype=np.int64)
        else:es=r.integers(1,4096,int(w),dtype=np.int64)
        S[i]=np.bitwise_xor.reduce(EXP[(LOG[es][None,:]+np.arange(1,71)[:,None]*pos[None,:])%4095],axis=1)
        if mode=='confluent':assert not S[i,:int(w)-1].any() and S[i,int(w)-1]==1
        if mode=='onehot':M[i].fill(0);M[i,pos[0]]=1<<(i%12)
        p[i]=sum(int(a).bit_count() for a in es&M[i,pos])&1
    return S,M,p
def panels(n):
    for j,mode in enumerate(('dense','zero','onehot','confluent')):
        for k in range(4):
            yield mode,np.repeat(np.arange(36),2),320211+j*100+k,971+k
    k=np.arange(36,dtype=float);off=np.sqrt(k[1:]*(4095-k[1:]+1));d=64/math.sqrt(2016*(4096-2016))
    _,ev=np.linalg.eigh(np.diag(k*d)+np.diag(off,1)+np.diag(off,-1));prob=np.abs(ev[:,-1])**2;prob/=prob.sum()
    for j in range(0,n,128):
        w=np.random.default_rng(310370+j).choice(36,min(128,n-j),p=prob)
        yield 'distribution',w,983210+j,7751+j

def run(path,out,n,shell=False):
    c=km.Circuit.from_file(str(path));reg=c.register_data
    assert set(reg)=={f'S{i}' for i in range(70)}|{f'E{j}' for j in range(4095)}
    q=km.array([v for i in range(70) for v in reg[f'S{i}']])
    mask=km.array([v for j in range(4095) for v in reg[f'E{j}']])
    qs=set(q);anc=km.array([km.q(i) for i in range(c.num_qubits) if km.q(i) not in qs])
    result=dict(sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),shell=shell,q=c.num_qubits,static_paid=int(c.operation_statistics().num_toffoli_like),ops=len(c),panels={},failures=[])
    for mode,w,seed,coin in panels(n):
        S,M,P=make(w,mode,seed);target=np.zeros_like(P) if shell else P
        row=result['panels'].setdefault(mode,dict(shots=0,errors=[0]*4,union=0,paid=0))
        A,B=bits(S),bits(M);s=km.Simulator(batch_size=len(w),seed=coin,debug_print=False,counting_operations=True)
        s.use_same_registers_as(c);s.write_across_shots(q,A);s.write_across_shots(mask,B);s.do(c)
        errs=np.array([(s.read_across_shots(q)!=A).any(0),s.read_phase_flipped_across_shots()^target,s.read_across_shots(anc).any(0),(s.read_across_shots(mask)!=B).any(0)])
        row['shots']+=len(w);row['errors']=(np.asarray(row['errors'])+errs.sum(1)).tolist();row['union']+=int(errs.any(0).sum());row['paid']+=int(s.operation_statistics().num_toffoli_like)
        for i in np.flatnonzero(errs.any(0)):
            result['failures'].append(dict(mode=mode,seed=seed,coin=coin,index=int(i),weight=int(w[i]),errors=errs[:,i].tolist(),S=S[i].tolist(),mask=M[i].tolist()))
        print(mode,seed,row['errors'],flush=True)
        out.write_text(json.dumps(result,indent=2)+'\n')
    for row in result['panels'].values():row['mean_paid']=row['paid']/row['shots']
    result['strict_zero']=all(not row['union'] for row in result['panels'].values())
    out.write_text(json.dumps(result,indent=2)+'\n')
    print('COMPLETE',json.dumps({k:v for k,v in result.items() if k!='failures'}),flush=True)
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('receipt',type=Path);p.add_argument('--shell',action='store_true');p.add_argument('--distribution',type=int,default=1024);a=p.parse_args()
    assert a.distribution>0
    r=run(a.path,a.receipt,a.distribution,a.shell)
    if not r['strict_zero']:raise SystemExit('FAIL: full-circuit counterexample retained')
if __name__=='__main__':main()
