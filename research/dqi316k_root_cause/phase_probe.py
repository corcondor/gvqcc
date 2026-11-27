"""Paired full native DQI zero/one-hot mask probe.
Usage: PYTHONPATH=<KickMix 1.0.0>:<official verifier dir> python phase_probe.py file.kmb receipt.json.
Same syndrome and seed. Matching seeds alone do not certify identical internal HMR trajectories.
"""
import sys, json, hashlib, pathlib
import numpy as np
import kickmix as km
import verify_submission_dqi as V
P=pathlib.Path(sys.argv[1]); O=pathlib.Path(sys.argv[2])
rng=np.random.default_rng(202611280337); t=V.FieldTables(km.GF2Field(12))
S=[]; M=[]; E=[]; L=[]
for w in (0,1,2,6,17,18,35):
    pos=rng.choice(4095,w,replace=False); val=rng.integers(1,4096,w,dtype=np.int64)
    a=np.bitwise_xor.reduce(t.antilog[(t.log[val][None,:]+np.arange(1,71)[:,None]*pos[None,:])%4095],axis=1) if w else np.zeros(70,dtype=np.int64)
    truth=dict(zip(map(int,pos),map(int,val)))
    points=list(dict.fromkeys(list(map(int,pos[:1]))+list(map(int,pos[-1:]))+[next(i for i in range(4095) if i not in truth)]))
    for j in points:
        for bit in range(12):
            mask=np.zeros(4095,dtype=np.int64);mask[j]=1<<bit
            S.append(a);M.append(mask);E.append(bool(truth.get(j,0)&(1<<bit)));L.append((w,j,bit,truth.get(j,0)))
S=np.array(S);M=np.array(M);E=np.array(E); A=V.to_bits(S,12); B=V.to_bits(M,12);Z=np.zeros_like(B)
c=km.Circuit.from_file(str(P));sp=V.ProblemSpecDQI.benchmark_instance(num_shots=len(S));q,b,anc=map(km.array,V.validate_registers(c,sp))
res={'file':str(P),'sha256':hashlib.file_digest(P.open('rb'),'sha256').hexdigest(),'Q':c.num_qubits,'ops':len(c),'num_paired_probes':len(S),'seed':202611280338,'cases':[],'official_verifier':False}
def run(bits):
    s=km.Simulator(batch_size=len(S),seed=res['seed'],debug_print=False,counting_operations=True)
    s.use_same_registers_as(c);s.write_across_shots(q,A);s.write_across_shots(b,bits);s.do(c)
    return (s.read_across_shots(q),s.read_across_shots(b),s.read_across_shots(anc),np.asarray(s.read_phase_flipped_across_shots(),dtype=bool),s.operation_statistics().num_toffoli_like)
a0,m0,d0,p0,t0=run(Z);a1,m1,d1,p1,t1=run(B)
actual=p0^p1;ve0=(a0!=A).any(0);ve1=(a1!=A).any(0);me0=(m0!=Z).any(0);me1=(m1!=B).any(0);de0=d0.any(0);de1=d1.any(0)
res.update(zero_phase_errors=int(p0.sum()),mask_phase_difference_errors=int((actual!=E).sum()),output_value_mask_dependence=int((a0!=a1).any(0).sum()),zero_mask_restore_errors=int(ve0.sum()),onehot_restore_errors=int(ve1.sum()),zero_mask_dirty=int(de0.sum()),onehot_dirty=int(de1.sum()),mask_restore_errors=int(me0.sum()+me1.sum()),paired_paid=[int(t0),int(t1)])
for w,j in sorted(set((r[0],r[1]) for r in L)):
    ii=[i for i,r in enumerate(L) if r[:2]==(w,j)]
    guess=sum(int(actual[i])<<L[i][2] for i in ii);truth=L[ii[0]][3]
    bits=a0[:,ii[0]].astype('int64').reshape(70,12);syndrome_out=(bits*(1<<np.arange(12))).sum(1).tolist()
    res['cases'].append(dict(weight=w,position=j,expected_magnitude=truth,phase_difference_word=guess,zero_mask_phase_errors=int(p0[ii].sum()),value_errors=int(ve0[ii].sum()),output_syndrome=syndrome_out,initial_syndrome=S[ii[0]].tolist()))
O.write_text(json.dumps(res,indent=2)+'\n')
print({k:v for k,v in res.items() if k!='cases'})
