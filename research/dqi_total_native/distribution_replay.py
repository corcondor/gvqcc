import math, sys, json, hashlib
import numpy as np
import kickmix as km
from verify import bits
from crt882 import exp,log,moment
path=sys.argv[1];N=int(sys.argv[2]) if len(sys.argv)>2 else 1024
c=km.Circuit.from_file(path)
q=km.array([v for i in range(70) for v in c.register_data[f'S{i}']])
b=km.array([v for i in range(4095) for v in c.register_data[f'E{i}']])
qs=set(q);a=km.array([km.q(j) for j in range(c.num_qubits) if km.q(j) not in qs])
k=np.arange(36,dtype=float); off=np.sqrt(k[1:]*(4095-k[1:]+1));d=64/math.sqrt(2016*2080)
_,ev=np.linalg.eigh(np.diag(k*d)+np.diag(off,1)+np.diag(off,-1))
p=ev[:,-1]**2;p/=p.sum()
rng=np.random.default_rng(202611280846);E=np.zeros(4,dtype=np.int64);paid=0;union=0
for st in range(0,N,128):
 n=min(128,N-st);w=rng.choice(36,n,p=p);M=rng.integers(0,4096,(n,4095),dtype=np.uint16);S=[];ph=[]
 for i,v in enumerate(w):
  ix=rng.choice(4095,int(v),replace=False);xs=[exp[j] for j in ix];es=rng.integers(1,4096,int(v));S.append(moment(xs,list(map(int,es))));ph.append(sum((int(x)&int(y)).bit_count() for x,y in zip(es,M[i,ix]))&1)
 X=bits(S);Y=bits(M);sim=km.Simulator(batch_size=n,seed=846+st,counting_operations=True,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,X);sim.write_across_shots(b,Y);sim.do(c)
 err=np.array([(sim.read_across_shots(q)!=X).any(0),(sim.read_across_shots(b)!=Y).any(0),sim.read_across_shots(a).any(0),np.asarray(sim.read_phase_flipped_across_shots(),bool)!=np.asarray(ph,bool)])
 E+=err.sum(1);union+=int(err.any(0).sum());paid+=int(sim.operation_statistics().num_toffoli_like)
 print(st+n,E.tolist(),flush=True)
r=dict(scope='independent ordinary distribution; not official verifier',sha256=hashlib.file_digest(open(path,'rb'),'sha256').hexdigest(),shots=N,Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),mean_paid=paid/N,errors_order=['value','mask','dirty','phase'],errors=E.tolist(),union=union)
print(json.dumps(r),flush=True);open('distribution_receipt.json','w').write(json.dumps(r,indent=2)+'\n')
