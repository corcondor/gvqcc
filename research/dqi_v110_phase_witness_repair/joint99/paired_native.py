"""Matched KickMix archive replay: do not treat finite panels as correctness proof."""
import sys,hashlib,json,struct
import numpy as np
import kickmix as km
import verify_submission_dqi as V
def read_eight(f,rows,n):
 b=f.read(8*rows);assert len(b)==8*rows
 return np.unpackbits(np.frombuffer(b,dtype=np.uint8).reshape(rows,8),axis=1,bitorder='little')[:,:n].astype(bool)
def data(path):
 if path=='ordinary8192':
  spec=V.ProblemSpecDQI.benchmark_instance(); t=V.FieldTables(km.GF2Field(spec.degree))
  for j in range(8):
   v,b,e=V.sample_shots(spec,t,np.random.default_rng(202611281021+j),1024)
   yield (1024,V.to_bits(v,spec.degree),V.to_bits(b,spec.degree),e)
  return
 with open(path,'rb') as f:
  for _ in range(struct.unpack('<I',f.read(4))[0]):
   n=struct.unpack('<I',f.read(4))[0]
   yield (n,read_eight(f,840,n),read_eight(f,49140,n),read_eight(f,1,n)[0])
  assert not f.read(1)
def compare(fixture,paths,expected_same=True):
 outputs=[]
 for path in paths:
  c=km.Circuit.from_file(path,format='kmb')
  q,b,a=map(km.array,V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance()))
  pays={k:0 for k in ('CCX','CCZ','CSWAP')};hashes=[];counts=np.zeros(5,dtype=int);shots=0
  for j,(n,X,Y,P) in enumerate(data(fixture)):
   s=km.Simulator(n,seed=202611280853+j,debug_print=False,counting_operations=True)
   s.use_same_registers_as(c);s.write_across_shots(q,X);s.write_across_shots(b,Y);s.do(c)
   x,y,r,p=s.read_across_shots(q),s.read_across_shots(b),s.read_across_shots(a),s.read_phase_flipped_across_shots()
   fields=np.array([(x^X).any(0),(p^P),r.any(0),(y^Y).any(0)])
   counts+=np.concatenate((fields.sum(1),[fields.any(0).sum()]))
   h=hashlib.sha256()
   for m in (x,y,r,p):h.update(m.tobytes())
   hashes.append(h.hexdigest());stats=dict(s.operation_statistics());shots+=n
   for k in pays:pays[k]+=int(stats.get(k,0))
  result=dict(arm=path,shots=shots,Q=c.num_qubits,ops=len(c),errors=counts.tolist(),paid=pays,mean_paid=sum(pays.values())/shots)
  if outputs:result['all_output_fields_match']=outputs[0]==hashes
  if outputs and expected_same:assert outputs[0]==hashes
  print(json.dumps(result),flush=True)
  outputs.append(hashes)
  del c,s
if __name__=='__main__':compare(sys.argv[1],sys.argv[2:])
