"""Classical #261 raw-to-half adapter; native phase on its actual output.
No claim of a physical adapter or shell splice.
"""
import json,struct,zipfile,hashlib
from pathlib import Path
import numpy as np,kickmix as km
import verify_half as v

def panels():
    a=zipfile.ZipFile('GVQCC_316K_RANK15_FULL_SPLICE_SOURCE_RECEIPTS.zip')
    for g in ('saved','cross','fresh','cross_inverse_frob4'):
        with a.open(f'joint_work/audit/{g}.bin') as f:
            for i in range(struct.unpack('<I',f.read(4))[0]):
                n=struct.unpack('<I',f.read(4))[0];f.read(840*8)
                def unpack(l):return np.unpackbits(np.frombuffer(f.read(l*8),np.uint8).reshape(l,8),axis=1,bitorder='little')[:,:n]
                yield g,i,unpack(49140).astype(bool),unpack(1)[0].astype(bool)
    w=json.loads(Path('GVQCC_DQI_w33_423bit_witness.json').read_text())
    e=dict(zip(w['error_indices'],w['error_values']))
    m=np.zeros((49140,1+12*len(e)),bool)
    for i,j in enumerate(e):
        for t in range(12):m[12*j+t,12*i+t+1]=1
    ph=np.array([0,*[(c>>t)&1 for c in e.values() for t in range(12)]],bool)
    for i in range(0,len(ph),64):yield 'w33',i,m[:,i:i+64],ph[i:i+64]

def main():
    file='half.kmb';p=v.sha(file);assert p=='72676a49be105adc303d0c4541b1beba09665aa9421c41f67649d4c064e5c6fa'
    c=km.Circuit.from_file(file);u=json.loads(Path('public_weight.json').read_text())
    dn={}
    for l in Path('raw_words.jsonl').read_text().splitlines():
        g,b,i,w,z,gg,gn,D,N,k=json.loads(l)
        assert gg==[1] and z==D[-1]!=0
        D=[v.m(x,v.F.inv(z)) for x in D];N=[v.m(x,v.F.inv(z)) for x in N]
        H,V=v.half(D,N);dn[g,b,i]=D[:-1]+H
    # #246 scan already carries factor x^-1 in the emitted mask. Add only U_pub^-1.
    A=np.array([[(v.m(v.F.inv(v.F.evalpoly(u,x)),1<<i)>>j)&1 for i in range(12) for j in range(12)] for x in v.F.EXP[:4095]],np.uint8).reshape(4095,12,12)
    q=km.array([km.q(i) for i in range(840)]);a=km.array([km.q(i) for i in range(840,851)]);b=km.array([km.b(i) for i in range(49140)])
    out={}
    for g,k,m,z in panels():
        n=len(z);x=v.bits([dn[g,0 if g=='w33' else k,0 if g=='w33' else i] for i in range(n)])
        mm=(np.einsum('aij,ajn->ain',A,m.reshape(4095,12,n),dtype=np.uint8)%2).reshape(49140,n).astype(bool)
        out0=out.setdefault(g,dict(shots=0,errors=[0,0,0,0],paid=0))
        for seed in (64571,64572):
            s=km.Simulator(batch_size=n,seed=seed+k,counting_operations=True,debug_print=False);s.use_same_registers_as(c);s.write_across_shots(q,x);s.write_across_shots(b,mm);s.do(c)
            e=[(s.read_across_shots(q)!=x).any(0),s.read_phase_flipped_across_shots()^z,s.read_across_shots(a).any(0),(s.read_across_shots(b)!=mm).any(0)]
            out0['errors']=(np.array(out0['errors'])+np.array([v0.sum() for v0 in e])).tolist();out0['shots']+=n;out0['paid']+=int(s.operation_statistics().num_toffoli_like)
    print(json.dumps(out),flush=True)
    Path('weighted_adapter_receipt.json').write_text(json.dumps(dict(scope='measured native #246 fed classical frame from measured #261 native prefix; no physical adapter or shell splice',sha=p,panels=out),indent=2)+'\n')
if __name__=='__main__':main()
