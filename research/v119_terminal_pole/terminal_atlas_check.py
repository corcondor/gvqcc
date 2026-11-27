#!/usr/bin/env python3
"""Exhaustive classical GF(4096) terminal atlas; not a KMB."""
import json
import numpy as np

Q=4096
M=4095
MOD=0x1053
LOG=np.full(Q,-1,np.int32)
EXP=np.zeros(2*M,np.uint16)
x=1
for i in range(M):
    assert LOG[x]<0
    LOG[x]=i
    EXP[i]=x
    x <<= 1
    if x&Q:
        x ^= MOD
assert x==1
EXP[M:]=EXP[:M]
INV=np.zeros(Q,np.uint16)
INV[1:]=EXP[M-LOG[1:]]

def mul(a,b):
    a,b=np.asarray(a),np.asarray(b)
    return np.where((a!=0)&(b!=0),EXP[LOG[a]+LOG[b]],0).astype(np.uint16)

def run():
    words=np.arange(Q,dtype=np.uint16)
    nodes=[int(mul(2*i,2*i))^(2*i)^2048 for i in range(17)]
    assert len(set(nodes))==17
    results=[]
    for k in nodes:
        c=mul(k,k)
        assert c
        u=mul(c,INV)
        scale=mul(c,mul(INV,INV))
        scale[0]=1
        assert np.array_equal(mul(c,INV[u]),words)
        assert np.all(mul(scale[1:],scale[u[1:]])==1)
        zero_row=mul(c,INV)
        assert np.array_equal(zero_row[zero_row],words)
        for first in range(0,Q,256):
            n=words[first:first+256]
            v=mul(scale[n,None],words[None,:])
            if first==0:
                v[0]=zero_row
            recovered=mul(scale[u[n],None],v)
            if first==0:
                recovered[0]=zero_row[v[0]]
            assert np.array_equal(recovered,np.broadcast_to(words,recovered.shape))
        results.append(dict(kappa=k,pairs=Q**2,errors=0,extra_tag_bits=0))
    return dict(scope="classical field-pair involution; not native phase correctness",
                results=results,total_pairs=len(nodes)*Q**2)
if __name__=="__main__":
    print(json.dumps(run(),indent=2))
