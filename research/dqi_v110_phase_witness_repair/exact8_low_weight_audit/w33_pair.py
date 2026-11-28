import sys, json, hashlib
from pathlib import Path
import numpy as np, kickmix as km
import verify_submission_dqi as V
import direct_codec as D
w=json.loads(Path(sys.argv[1]).read_text())
sp=V.ProblemSpecDQI.benchmark_instance(num_shots=64)
tab=V.FieldTables(km.GF2Field(12))
N=64
pos=np.array(w['error_indices']); val=np.array(w['error_values'])
old={x['circuit']:x for x in w['native_rows']}
s=np.array(w['native_rows'][0]['input'])
refs=np.array(D.moments({int(tab.antilog[p]):int(v) for p,v in zip(pos,val)}))
assert np.array_equal(refs,s)
rng=np.random.default_rng(78493)
m=rng.integers(0,4096,size=(N,sp.m),dtype=np.uint16)
m[0]=0;m[1:34]=0
for i,p in enumerate(pos):m[1+i,p]=4095
exp=np.array([sum(int(x).bit_count() for x in (val&l[pos]))&1 for l in m],bool)
sx=V.to_bits(np.tile(s,(N,1)),12); mx=V.to_bits(m,12)
receipt={}
for p in sys.argv[2:]:
  c=km.Circuit.from_file(p); q,b,a=map(km.array,V.validate_registers(c,sp))
  sim=km.Simulator(batch_size=N,seed=78493,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,sx);sim.write_across_shots(b,mx);sim.do(c)
  sout=np.asarray(sim.read_across_shots(q));phase=np.array(sim.read_phase_flipped_across_shots()); anc=np.asarray(sim.read_across_shots(a)); mask=np.asarray(sim.read_across_shots(b))
  coeff=sout.T.reshape(N,70,12)@np.left_shift(1,np.arange(12))
  receipt[Path(p).name]=dict(input_shots=N,syndrome_errors=int(np.any(sout!=sx,axis=0).sum()),phase_errors=int((phase!=exp).sum()),dirty_errors=int(np.any(anc,axis=0).sum()),mask_errors=int(np.any(mask!=mx,axis=0).sum()),syndrome_bit_counts=sorted(set(map(int,(sout!=sx).sum(axis=0)))),distinct_residuals=len(np.unique(coeff^s,axis=0)),matched_old_residuals={k:int(np.all((coeff^s)==v['residual'],axis=1).sum()) for k,v in old.items()}, output_digest=hashlib.sha256(sout.tobytes()).hexdigest(), phase_digest=hashlib.sha256(phase.tobytes()).hexdigest())
  print(json.dumps(receipt[Path(p).name]),flush=True)
Path('w33_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
