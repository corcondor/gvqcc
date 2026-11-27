import json, hashlib, time, sys, collections
import numpy as np
import kickmix as km
import verify_half as V
t=time.time()
c=km.Circuit.from_file('full.kmb',format='kmb')
print('loaded',c.num_qubits,len(c),flush=True)
assert c.num_qubits==900
assert set(c.register_data)=={f'S{i}' for i in range(70)}|{f'E{i}' for i in range(4095)}
q=km.array([km.q(i) for i in range(840)])
anc=km.array([km.q(i) for i in range(840,900)])
mreg=km.array([km.b(i) for i in range(49140)])
rng0=__import__('random').Random(316028)
rows=[('stratified',w,{j:rng0.randrange(1,4096) for j in rng0.sample(range(4095),w)}) for w in range(36) for _ in range(16)]
# Keep the pre-existing all-pole and constant-numerator adversaries.
rows+= [r for r in V.fixtures() if r[0]!='random']
# Put one of each weight in the first two batches.
rows.sort(key=lambda r:(r[0]!='random',r[1]))
seen=set();first=[];rest=[]
for r in rows:
 if r[1] not in seen:seen.add(r[1]);first.append(r)
 else:rest.append(r)
rows=first+rest
rng=np.random.default_rng(23198)
err=np.zeros(4,dtype=int);groups=collections.Counter();paid=0;shots=0
for seed in (81628,):
 for i in range(0,len(rows),32):
  batch=rows[i:i+32];n=len(batch)
  M=rng.integers(0,4096,(n,4095),dtype=np.uint16)
  for k,(_,w,e) in enumerate(batch):
   if w==0 or (i+k)%4==0:M[k]=0
   elif (i+k)%4==1:
    M[k]=0;pos=next(iter(e),0);M[k,pos]=1<<((i+k)%12)
  arr=V.bits([V.moments(e) for _,_,e in batch]);mb=V.bits(M)
  phase=np.array([sum((int(M[k,j])&v).bit_count() for j,v in e.items())%2 for k,(_,_,e) in enumerate(batch)],bool)
  sim=km.Simulator(batch_size=n,seed=seed+i,debug_print=False,counting_operations=True)
  sim.use_same_registers_as(c);sim.write_across_shots(q,arr);sim.write_across_shots(mreg,mb);sim.do(c)
  es=[(sim.read_across_shots(q)!=arr).any(0),sim.read_across_shots(anc).any(0),(sim.read_across_shots(mreg)!=mb).any(0),sim.read_phase_flipped_across_shots()!=phase]
  err+=np.array([e.sum() for e in es]);shots+=n;paid+=int(sim.operation_statistics().num_toffoli_like)
  groups.update(f'{tag}:w{w}' for tag,w,e in batch)
  print('batch',seed,i,n,'errors',err.tolist(),'seconds',round(time.time()-t,2),flush=True)
  rec=dict(Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),shots=shots,errors=err.tolist(),groups=dict(groups),mean_paid=paid/shots,sha256=V.sha('full.kmb'),seconds=time.time()-t)
  open('native_stress_receipt.json','w').write(json.dumps(rec,indent=2))
  if any(err):
   print('FAIL',[(batch[k][0:2], [bool(e[k]) for e in es]) for k in range(n) if any(e[k] for e in es)],flush=True);sys.exit(1)
print('DONE',shots,err.tolist(),paid/shots,flush=True)
