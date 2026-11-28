import sys,json,hashlib
import numpy as np
import kickmix as km
from verify_submission_dqi import ProblemSpecDQI, FieldTables, sample_shots, validate_registers, to_bits
spec=ProblemSpecDQI.benchmark_instance()
rng=np.random.default_rng(2026112800)
tables=FieldTables(km.GF2Field(spec.degree))
for arm,path in enumerate(sys.argv[1:]):
 c=km.Circuit.from_file(path,format='kmb')
 S,E,A=validate_registers(c,spec); S,E=km.array(S),km.array(E)
 stats={}
 rows=[]
 for j in range(4):
  n=256 if j<3 else 272
  rg=np.random.default_rng(2026112800+j)
  if j<3: sy,mb,e=sample_shots(spec,tables,rg,n)
  else:
   panels=[sample_shots(spec,tables,rg,8,np.eye(spec.max_errors+1)[w]) for w in range(1,35)]
   sy,mb,e=map(np.concatenate,zip(*panels))
  sb,eb=to_bits(sy,spec.degree),to_bits(mb,spec.degree)
  z=km.Simulator(n,counting_operations=True,seed=182850+j,debug_print=False)
  z.use_same_registers_as(c)
  z.write_across_shots(S,sb);z.write_across_shots(E,eb);z.do(c)
  sy_out=z.read_across_shots(S);mb_out=z.read_across_shots(E);an=z.read_across_shots(A);ph=z.read_phase_flipped_across_shots()
  check=hashlib.sha256()
  for a in (sy_out,mb_out,an[:60],ph):check.update(a.tobytes())
  d=dict(n=n,batch=j,path=path,width=c.num_qubits,native_ops=len(c),hash=check.hexdigest(),value=int(((sy_out!=sb).any(axis=0)|an.any(axis=0)).sum()),phase=int((e^ph).sum()),mask=int((mb_out!=eb).any(axis=0).sum()),dirty=int(an.any(axis=0).sum()),**{k:int(v) for k,v in z.operation_statistics().items() if k in ('CCX','CCZ','CSWAP','CX')})
  if arm and j<len(prior):
   assert d['hash']==prior[j]['hash'] and d['CCX']==prior[j]['CCX'] and d['CCZ']==prior[j]['CCZ']
   d['markers_per_shot']=(d['CSWAP']-prior[j]['CSWAP'])/n
  rows.append(d)
  print(json.dumps(d),flush=True)
 prior=rows
 del c
