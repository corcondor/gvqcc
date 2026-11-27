import pathlib,sys,json,hashlib,time
import kickmix as km
import numpy as np
import crt882 as C
sys.path.insert(0,'/tmp/fusion/google-verifiable-quantum-circuit-compilation/verifiers/dqi')
import verify_submission_dqi as V
P=pathlib.Path(sys.argv[1]);out=P.with_suffix('.verification.json');c=km.Circuit.from_file(str(P))
spec=V.ProblemSpecDQI.benchmark_instance();table=V.FieldTables(km.GF2Field(12))
q,e,anc=map(km.array,V.validate_registers(c,spec))
rng=np.random.default_rng(24620261128);res={'Q':c.num_qubits,'ops':len(c),'static_paid':int(c.operation_statistics().num_toffoli_like),'sha256':hashlib.file_digest(P.open('rb'),'sha256').hexdigest(),'panels':{}}
def forced():
 rows=[];es=[];masks=[];phase=[]
 for typ,n in [('uniform',288),('constant_numerator',35),('allpole',24),('singlepole',96)]:
  S=[];M=[];F=[]
  for i in range(n):
   w=i%36 if typ=='uniform' else i+1 if typ=='constant_numerator' else 35
   ix=rng.choice(4095,w,replace=False);xs=[int(table.antilog[j]) for j in ix]
   vals=[int(x) for x in rng.integers(1,4096,w)]
   if typ!='uniform':
    D=[1]
    for x in xs:D=C.mul(D,[x,1])
    dd=[int(D[i]) if i%2 else 0 for i in range(1,len(D))]
    if typ=='allpole':g=C.G
    elif typ=='singlepole':g=[int(C.ks[i%len(C.ks)]),1,1]
    else:g=[1]
    vals=[C.inv(C.m(C.m(x,C.evalp(dd,x)),C.evalp(g,x))) for x in xs]
   mask=rng.integers(0,4096,4095,dtype=np.int64)
   if i%4==0:mask[:]=0
   if i%4==1:
    mask[:]=0
    if w:mask[ix[0]]=1<<(i%12)
   S.append(C.moment(xs,vals));M.append(mask);F.append(bool(sum((int(mask[j])&v).bit_count() for j,v in zip(ix,vals))%2))
  yield typ,np.asarray(S,np.int64),np.asarray(M,np.int64),np.asarray(F,bool)
def run(name,S,M,F,seed):
 z={'shots':len(S),'value':0,'phase_raw':0,'ancilla':0,'mask':0,'union':0,'paid':0};res['panels'][name]=z
 for st in range(0,len(S),64):
  en=min(st+64,len(S));a=V.to_bits(S[st:en],12);m=V.to_bits(M[st:en],12)
  sim=km.Simulator(batch_size=en-st,seed=seed+st,counting_operations=True,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,a);sim.write_across_shots(e,m);sim.do(c)
  ve=(sim.read_across_shots(q)!=a).any(0);ph=np.asarray(sim.read_phase_flipped_across_shots(),bool)^F[st:en];di=sim.read_across_shots(anc).any(0);ma=(sim.read_across_shots(e)!=m).any(0)
  for key,v in [('value',ve),('phase_raw',ph),('ancilla',di),('mask',ma),('union',ve|ph|di|ma)]:z[key]+=int(v.sum())
  z['paid']+=int(sim.operation_statistics().num_toffoli_like);del sim
  print(name,en,'/',len(S),'errors',z['union'],flush=True);out.write_text(json.dumps(res,indent=2))
 z['mean_paid']=z['paid']/len(S)
 eps=V.clopper_pearson_upper_bound(z['union'],len(S))
 if eps<1/16:
  z['cp_upper']=eps;z['repetition']=V.repetition_overhead(eps);z['diagnostic_cost']=c.num_qubits**2*z['mean_paid']*z['repetition']
 out.write_text(json.dumps(res,indent=2))
 print('PANEL',json.dumps(z),flush=True)
for name,S,M,F in forced():run(name,S,M,F,24601)
S,M,F=V.sample_shots(spec,table,rng,1024);run('distribution_1024',S,M,F,24602)
print('DONE',json.dumps(res),flush=True)

