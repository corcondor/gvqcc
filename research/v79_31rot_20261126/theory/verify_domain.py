"""Independent legal-domain native replay and modular phase verification.

Adapted transparently from recovered/V79/verify_echo.py. Only the input
truth-table domain changes: states outside x=1..3,133,452 are excluded.
Every actual rotated wire, HMR phase debt, and restored input/work wire is
checked on the complete legal domain. The separate phase contraction checks
the declared tag expression on the full cube; it is linked to the actual
circuit only on the legal domain. This is not a full-cube circuit claim.
Run from recovered/V79, as with the donor verifier.
"""
import json,struct,sys,time,math,hashlib,subprocess
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"recovered/V79"))
from native_kmb import NativeKMB
import numpy as np
W=22;N=3133452;L=1<<W;MOD=1<<128

def input_masks():
 out=[]
 for q in range(W):
  if q<3:b=bytes([[0xaa,0xcc,0xf0][q]])*(L//8)
  else:a=1<<(q-3);b=(bytes(a)+b'\xff'*a)*(L//(16*a))
  out.append(int.from_bytes(b,'little') & ((1 << (N+1))-2))
 return out

def verify(stem,planpath):
 t=time.time();P=json.load(open(planpath));T=json.load(open(stem+'.json'));K=NativeKMB.read(stem+'.kmb');ref=NativeKMB.read('reference_header.kmb');A=K.header;Q=A[1];assert 22<=Q<37 and A[2] in (0,1) and dict(K.sections)[0]==dict(ref.sections)[0] and dict(K.sections)[11]==dict(ref.sections)[11]
 angles=dict(K.sections)[10];assert len(K.ops)==A[4] and A[10]==len(T['tags']) and len(angles)==16*A[10]
 inp=input_masks();state=inp+[0]*(Q-W);ones=(1<<(N+1))-2;pc={};fc={};groups=defaultdict(lambda:defaultdict(int));ri=0;maxq=-1;pending=None;hmr_count=0;hmr_debts=0
 def parity(s):
  if s in pc:return pc[s]
  z=0;u=s
  while u:b=u&-u;z^=inp[b.bit_length()-1];u^=b
  if len(pc)>=128:pc.clear()
  pc[s]=z;return z
 def prefix(d,p):
  if (d,p) in fc:return fc[d,p]
  y=ones
  for q in range(W-d,W):y &= inp[q] if (p>>(q-W+d))&1 else ones^inp[q]
  fc[d,p]=y;return y
 def add_coset(d,p,s,V,H,a):
  assert a%(1<<len(V))==0
  coeff={s:a//(1<<len(V))}
  for v,h in zip(V,H):
   new={x^v:c*h for x,c in coeff.items()};assert not set(new)&set(coeff);coeff.update(new)
  for s,c in coeff.items():groups[d,p][s]+=c
 for i,o in enumerate(K.ops):
  w=o.wires;g=o.raw;maxq=max(maxq,*w);assert maxq<Q
  if pending is not None:assert g in (17,33,144,160)
  if g not in (80,144,160):assert o.condition is None and o.measurement is None
  if g==17:state[w[0]]^=ones
  elif g==33:state[w[1]]^=state[w[0]]
  elif g==49:state[w[2]]^=state[w[0]]&state[w[1]]
  elif g==80:
   assert pending is None and o.measurement==0 and o.condition is None
   pending=state[w[0]];state[w[0]]=0;hmr_count+=1
  elif g in (144,160):
   assert pending is not None and o.condition==0 and o.measurement is None
   prod=state[w[0]] if g==144 else state[w[0]]&state[w[1]]
   assert pending==prod,(i,w);pending=None;hmr_debts+=1
  elif g==19:
   a=int.from_bytes(angles[ri*16:ri*16+16],'little');assert a==int(T['angles'][ri]);tag=T['tags'][ri];kind,s,d,p,V,H=tag[:6]
   expected=parity(s);assert a%2==0
   if kind=='borrow_flag':
    assert s==0 and d>0;u=tag[7];assert W-d<=u<W;bb=(p>>(u-(W-d)))&1;original=int(tag[6]);assert a==(original*(1-2*bb))%MOD
    f=prefix(d,p)
    for v,h in zip(V,H):f &= (ones^parity(v)) if h==1 else parity(v)
    assert state[w[0]]==inp[u]^f,(i,ri,tag)
    add_coset(d,p,0,V,H,original);groups[0,0][0]+=a//2;groups[0,0][1<<u]-=a//2
   elif kind in ('product','borrow'):
    f=prefix(d,p)
    for v,h in zip(V,H):f &= (ones^parity(v)) if h==1 else parity(v)
    expected &= f;original=int(tag[6]);add_coset(d,p,s,V,H,original);add_coset(d,p,0,V,H,-original)
    if kind=='borrow':
     u=tag[7];assert W-d<=u<W;bb=(p>>(u-(W-d)))&1;assert a==(-2*original*(1-2*bb))%MOD
     expected^=inp[u];groups[0,0][0]+=a//2;groups[0,0][1<<u]-=a//2
    else:assert a==(-2*original)%MOD
    assert state[w[0]]==expected,(i,ri,tag)
   else:
    if kind in ('direct','toggle'):
     f=prefix(d,p)
     for v,h in zip(V,H):f &= (ones^parity(v)) if h==1 else parity(v)
     expected^=f;add_coset(d,p,s,V,H,a)
    elif kind=='complement':expected^=ones
    else:assert kind=='parity'
    assert state[w[0]]==expected,(i,ri,kind,s,d,p,V,H)
    if kind!='direct':groups[0,0][0]+=a//2;groups[0,0][s]+=(a//2 if kind=='complement' else -a//2)
    else:assert s==0
   ri+=1
  else:raise ValueError(o)
  if i%30000==0:print(stem,'ops',i,'sec',round(time.time()-t,2),flush=True)
 assert state==inp+[0]*(Q-W) and ri==A[10] and pending is None and hmr_count==hmr_debts
 del pc,fc,state,inp
 def write_groups(path,gs):
  with open(path,'wb') as f:
   f.write(struct.pack('<I',len(gs)))
   for (d,p),z in sorted(gs.items()):
    v=[(s,a%MOD) for s,a in z.items()if a%MOD];f.write(struct.pack('<III',d,p,len(v)))
    for s,a in v:f.write(struct.pack('<I',s)+a.to_bytes(16,'little'))
 expected=defaultdict(lambda:defaultdict(int));scale=MOD//P['scale'];cover=np.zeros(L,np.uint8)
 for b in P['blocks']:
  k=b['k'];st=b['start'];d=W-k;cover[st:st+(1<<k)]+=1
  for s,a in b['coeff'].items():expected[d,st>>k][int(s)]+=int(a)*scale
 assert np.all(cover[1:N+1]==1) and cover.max()==1
 write_groups(stem+'.actual.bin',groups);write_groups(stem+'.expected.bin',expected)
 subprocess.run(['./phasecheck',stem+'.actual.bin',stem+'.expected.bin',stem+'.phase.u128'],check=True)
 y=np.memmap(stem+'.phase.u128',dtype='<u8',shape=(L,2),mode='r');S=P['scale'];e=P['epsilon'];lo=(S-e)**2;hi=(S+e)**2;shift=64-(S.bit_length()-1)
 assert not y[1:N+1,0].any();assert not (y[1:N+1,1]&np.uint64((1<<shift)-1)).any()
 a=(y[1:N+1,1]>>np.uint64(shift)).astype(np.uint64)
 if a[0]<S//2:a[0]+=S
 bad=0;mx=0.;arg=0
 for x,v in enumerate(a,1):
  v=int(v);bad+=not(lo<=x*v*v<=hi);z=abs(v/S*math.sqrt(x)-1)*2**24
  if z>mx:mx=z;arg=x
 assert bad==0
 c=Counter(o.raw for o in K.ops);out=dict(stem=stem,sha256=hashlib.sha256(Path(stem+'.kmb').read_bytes()).hexdigest(),plan=planpath,width=Q,ops=len(K.ops),ccx=c[49],cx=c[33],x=c[17],rotations=ri,generic=sum(int(a)%(1<<125)!=0 for a in T['angles']),hmr=hmr_count,exact_independent_hmr_phase_cancellations=hmr_debts,checked_inputs=N,domain='legal_1_to_3133452',full_cube_equivalence=False,legal=N,tag_replay='PASS',input_restoration='PASS',phase_contraction='PASS: tag expression; circuit equality asserted only on legal inputs',exact_tolerance='PASS',worst_error_ratio=mx,worst_x=arg,official_verifier=False,seconds=time.time()-t)
 Path(stem+'.receipt.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
if __name__=='__main__':verify(sys.argv[1],sys.argv[2])
