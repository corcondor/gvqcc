import hashlib,json,sys
from pathlib import Path
import kickmix as km,numpy as np
import verify_submission_dqi as V
rng=np.random.default_rng(202611280456); field=V.FieldTables(km.GF2Field(12)); spec=V.ProblemSpecDQI.benchmark_instance()
W=np.repeat(np.arange(36),16); N=len(W)
S=np.zeros((N,70),dtype=np.int64); M=rng.integers(0,4096,(N,4095),dtype=np.int64); M[:8]=0; P=np.zeros(N,dtype=bool)
for i,w in enumerate(W):
 if w:
  a=rng.choice(4095,w,replace=False);e=rng.integers(1,4096,w);S[i]=np.bitwise_xor.reduce(field.antilog[(field.log[e][None,:]+np.arange(1,71)[:,None]*a[None,:])%4095],axis=1);P[i]=sum(int(v).bit_count() for v in (e&M[i,a]))%2
D,DM,DP=V.sample_shots(spec,field,rng,1024);panels=[('forced',S,M,P,W),('distribution',D,DM,DP,np.full(1024,-1))]
path=Path(sys.argv[1]);c=km.Circuit.from_file(str(path));q,b,anc=map(km.array,V.validate_registers(c,spec));print('loaded',path,c.num_qubits,len(c),flush=True)
rows=[]
for name,S,M,P,W in panels:
 for st in range(0,len(S),192):
  en=min(st+192,len(S));seed=202611280456+st;ib=V.to_bits(S[st:en],12);mb=V.to_bits(M[st:en],12);sim=km.Simulator(batch_size=en-st,seed=seed,counting_operations=True,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,ib);sim.write_across_shots(b,mb);sim.do(c)
  p=np.asarray(sim.read_phase_flipped_across_shots(),dtype=bool);v=(sim.read_across_shots(q)!=ib).any(0);d=sim.read_across_shots(anc).any(0);m=(sim.read_across_shots(b)!=mb).any(0)
  rows.append({'panel':name,'start':st,'weight':W[st:en].tolist(),'phase':p.tolist(),'expected':P[st:en].tolist(),'value':v.tolist(),'dirty':d.tolist(),'mask':m.tolist(),'paid':int(sim.operation_statistics().num_toffoli_like)})
  print(name,st,'phase bad',int((p^P[st:en]).sum()),'value',int(v.sum()),'dirty',int(d.sum()),'mask',int(m.sum()),flush=True);del sim
out={'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),'Q':c.num_qubits,'ops':len(c),'static_paid':int(c.operation_statistics().num_toffoli_like),'rows':rows};Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n')
