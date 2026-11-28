import sys,struct,hashlib,json
import kickmix as km
import numpy as np
import verify_submission_dqi as V
key=133
with open(f'independent/panel{key%4}.bin','rb') as f:
 for j in range(struct.unpack('<I',f.read(4))[0]):
  i,s=struct.unpack('<IQ',f.read(12))
  raw=f.read(64*(840+49140+1))
  if i==key:break
 else:raise RuntimeError('fixture missing')
A=np.unpackbits(np.frombuffer(raw,dtype=np.uint8).reshape(-1,64),axis=1,bitorder='little').astype(bool)
x,y,z=A[:840],A[840:-1],A[-1]
for p in sys.argv[1:]:
 C=km.Circuit.from_file(p,format='kmb')
 q,b,a=map(km.array,V.validate_registers(C,V.ProblemSpecDQI.benchmark_instance()))
 K=km.Simulator(512,seed=s,debug_print=False,counting_operations=True);K.use_same_registers_as(C)
 K.write_across_shots(q,x);K.write_across_shots(b,y);K.do(C)
 xx,yy,aa,zz=K.read_across_shots(q),K.read_across_shots(b),K.read_across_shots(a),K.read_phase_flipped_across_shots()
 d=(xx!=x).sum(0)
 report=dict(arm=p,batch=key,bad_value_positions=np.flatnonzero(d).tolist(),bad_value_bit_counts=d[d>0].tolist(),raw_phase_positions=np.flatnonzero(zz!=z).tolist(),dirty=int(aa.any(0).sum()),mask=int((yy!=y).any(0).sum()),mean_paid=K.operation_statistics().num_toffoli_like/512)
 print(json.dumps(report),flush=True)
 del C,K
