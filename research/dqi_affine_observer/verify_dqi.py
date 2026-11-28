import sys,json,hashlib,time,math
import numpy as np,kickmix as km
from scipy.stats import beta
from collections import defaultdict
exp=[];log=np.zeros(4096,dtype=np.int64);x=1
for i in range(4095):
 exp.append(x);log[x]=i;x<<=1
 if x&4096:x^=0x1053
assert x==1
ant=np.array(exp); ex=np.array(exp*2)
def mul(a,b):return np.where((a!=0)&(b!=0),ex[log[a]+log[b]],0)
def tr(a):
 z=0
 for _ in range(12):z^=int(a);a=mul(a,a)
 return z
mask=np.array([sum(tr(mul(a,1<<k))<<k for k in range(12)) for a in range(4096)])
assert len(set(mask.tolist()))==4096
def bits(v):return (((v[:,:,None]>>np.arange(12))&1)==1).transpose(1,2,0).reshape(-1,len(v))
def panel(weights,kind,seed):
 r=np.random.default_rng(seed);n=len(weights);S=np.zeros((n,70),np.int64);M=r.integers(0,4096,size=(n,4095));p=np.zeros(n,bool)
 if kind=='zero':M.fill(0)
 if kind=='dual':
  coeff=r.integers(0,4096,size=(n,70));v=np.zeros((n,4095),np.int64)
  for j in range(69,-1,-1):v=mul(v,ant[None,:])^coeff[:,j,None]
  M=mask[mul(v,ant[None,:])]
 for j,w in enumerate(weights):
  if not w:continue
  pos=r.choice(4095,size=w,replace=False);val=r.integers(1,4096,size=w);S[j]=np.bitwise_xor.reduce(ant[(log[val][None,:]+np.arange(1,71)[:,None]*pos[None,:])%4095],axis=1)
  p[j]=sum(int(x).bit_count() for x in val&M[j,pos])&1
 return S,M,p
k=np.arange(36,dtype=float);off=np.sqrt(k[1:]*(4095-k[1:]+1));d=64/math.sqrt(2016*(4096-2016));_,ev=np.linalg.eigh(np.diag(k*d)+np.diag(off,1)+np.diag(off,-1));p=np.abs(ev[:,-1])**2;p/=p.sum()
def run(path,panels):
 c=km.Circuit.from_file(path);reg=c.register_data;assert set(reg)=={f'S{i}' for i in range(70)}|{f'E{j}' for j in range(4095)}
 q=km.array([v for i in range(70) for v in reg[f'S{i}']]);b=km.array([v for j in range(4095) for v in reg[f'E{j}']]);qs=set(q);a=km.array([km.q(i) for i in range(c.num_qubits) if km.q(i) not in qs])
 result={'sha256':hashlib.file_digest(open(path,'rb'),'sha256').hexdigest(),'Q':c.num_qubits,'ops':len(c),'static_paid':int(c.operation_statistics().num_toffoli_like),'panels':{}}
 for kind,weights,rs,ss in panels:
  S,M,P=panel(weights,kind,rs);n=len(weights);sim=km.Simulator(batch_size=n,seed=ss,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);X=bits(S);Y=bits(M);sim.write_across_shots(q,X);sim.write_across_shots(b,Y);sim.do(c)
  E=np.array([(sim.read_across_shots(q)!=X).any(0),sim.read_phase_flipped_across_shots()^P,sim.read_across_shots(a).any(0),(sim.read_across_shots(b)!=Y).any(0)]);row=result['panels'].setdefault(kind,dict(shots=0,errors=[0]*4,union=0,paid=0,weight_errors={}))
  dig=hashlib.sha256()
  for rr in (sim.read_across_shots(q),sim.read_phase_flipped_across_shots(),sim.read_across_shots(a),sim.read_across_shots(b)):dig.update(np.packbits(np.asarray(rr,dtype=bool).ravel()).tobytes())
  row.setdefault('paired_digest',[]).append(dig.hexdigest())
  row['shots']+=n;row['errors']=(np.array(row['errors'])+E.sum(1)).tolist();row['union']+=int(E.any(0).sum());row['paid']+=int(sim.operation_statistics().num_toffoli_like)
  for w in sorted(set(weights)):
   u=np.asarray(weights)==w;key=str(w);z=row['weight_errors'].setdefault(key,[0,0]);z[0]+=int(u.sum());z[1]+=int(E[:,u].any(0).sum())
  print(path,kind,n,E.sum(1).tolist(),int(E.any(0).sum()),row['paid']/row['shots'],flush=True)
 for z in result['panels'].values():z['mean_paid']=z['paid']/z['shots']
 return result
panels=[]
for j,kind in enumerate(['zero','dual','dense']):
 for s in range(2):panels.append((kind,np.repeat(np.arange(36),2).tolist(),19316+j*100+s,771+s))
for j in range(8):panels.append(('distribution',np.random.default_rng(738+j).choice(36,256,p=p).tolist(),8738+j,8810+j))
# distribution uses dense uniformly random masks.
out={}
for path in sys.argv[1:]:
 out[path]=run(path,panels);open('/tmp/dual_receipt.json','w').write(json.dumps(out,indent=2))
print('DONE',flush=True)

