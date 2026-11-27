"""Exact 35-slot Hermite CF with adaptive nonzero pivot, on input moments only.
All unprocessed local jets use homogeneous transport. No padded cases/host
choice in the mathematical map. NOT a native reversible DQI circuit.
Companion research archive contains direct_codec, test_extension_padding,
later_three, fixtures and full native replay and selector sources.
"""
import json,random,functools,pathlib,sys,time
import numpy as np
import direct_codec as D
from test_extension_padding import em,m,F,K
from later_three import ei,lin,gval,divide,components,xor
ORDER=[3169,3257,3134,3302,3727,3671,3792,3592]+[k for k in D.NODES if k not in [3169,3257,3134,3302,3727,3671,3792,3592]]+[K]
SLOTS={k:2 if k!=K else 1 for k in ORDER}
assert sum(SLOTS.values())==35
U=D.pmul(D.U,D.g(K)); assert len(U)==71
Z={k:next(c|F for c in range(F)if m(c,c)^c^K==k)for k in ORDER}
Q={}
for k,z in Z.items():
 a=divide(U,z);Q[k]=(a,divide(a,z)) if SLOTS[k]==2 else (a,)
assert sum(map(len,Q.values()))==35

def initial(s):
 b={}
 for k,qs in Q.items():
  t=[xor(em(a,int(x))for a,x in zip(q,s))for q in qs]
  b[k]=(t[0],1,t[1] if len(t)==2 else 0,0)
 return b

def decode(s,verify_trace=False):
 jets=initial(s);remaining=SLOTS.copy();heads=[];choices=[];stats={'nonselected':0,'derivative_updates':0,'skips':0,'selected_inverse':0,'terminal_slots':0}
 while remaining:
  options=[k for k in remaining if jets[k][0]!=0]
  if not options:
   stats['terminal_slots']=sum(remaining.values());break
  k=options[0];stats['skips']+=list(remaining).index(k);z=Z[k];n,d,np_,dp=jets[k];h=em(d,ei(n));stats['selected_inverse']+=1
  hpoly=[(h&4095)^m(h>>12,z&4095),h>>12];heads.append((k,hpoly));choices.append(k)
  for l in list(remaining):
   a,b,ap,bp=jets[l]
   if l==k:
    remaining[l]-=1
    if not remaining[l]:del remaining[l];del jets[l];continue
    jets[l]=(bp^em(h,ap)^em(h>>12,a),a,0,0)
   else:
    H=lin(h,z,Z[l]);g=gval(k,Z[l]);assert g
    p=b^em(H,a);q=em(g,a)
    assert p or q
    if remaining[l]==2:
     jets[l]=(p,q,bp^em(H,ap)^em(h>>12,a),em(g,ap)^a);stats['derivative_updates']+=1
    else:jets[l]=(p,q,0,0)
    stats['nonselected']+=1
 n,d=[],[1]
 for k,h in reversed(heads):n,d=d,D.add(D.pmul(D.g(k),n),D.pmul(h,d))
 assert d
 inv=D.inv(d[-1]);n=[m(x,inv)for x in n];d=[m(x,inv)for x in d]
 if verify_trace:
  a,b=n,d
  for k,h in heads:
   nr,dr=D.rem(a,k),D.rem(b,k);assert nr
   q,r=D.divrem(D.add(b,D.pmul(h,a)),D.g(k));assert not r;a,b=q,a
  assert not a and len(b)==1
 return n,d,stats,choices

EX=np.asarray(D.EXP,np.int32);LG=np.asarray(D.LOG,np.int32);XS=np.arange(1,F,dtype=np.int32)
def vm(a,b):
 a=np.asarray(a,dtype=np.int32);b=np.asarray(b,dtype=np.int32)
 return np.where((a!=0)&(b!=0),EX[LG[a]+LG[b]],0)
def evs(p,x=XS):
 v=np.zeros(len(x),np.int32)
 for y in reversed(p):v=vm(v,x)^int(y)
 return v
UX=evs(U);assert np.all(UX)
def errors(n,d):
 xs=XS[evs(d)==0]
 assert len(xs)==len(d)-1
 der=[d[i] if i%2 else 0 for i in range(1,len(d))]
 ns=evs(n,xs);ds=vm(vm(evs(der,xs),xs),UX[xs-1]);assert np.all(ds) and np.all(ns)
 es=vm(ns,EX[4095-LG[ds]]);return dict(zip(map(int,xs),map(int,es)))
def phase(e,M):return sum((a&int(M[D.LOG[x]])).bit_count()for x,a in e.items())%2

def linear_rank():
 A=[]
 for k,qs in Q.items():
  for q in qs:
   pad=q+[0]*(70-len(q));A.extend([[a&4095 for a in pad],[a>>12 for a in pad]])
 r=0;A=[list(x)for x in A]
 for j in range(70):
  p=next((k for k in range(r,70)if A[k][j]),None)
  if p is None:continue
  A[p],A[r]=A[r],A[p];inv=D.inv(A[r][j]);A[r]=[m(inv,x)for x in A[r]]
  for i in range(r+1,70):
   c=A[i][j]
   if c:A[i]=[a^m(c,b)for a,b in zip(A[i],A[r])]
  r+=1
 return r

def main():
 start=time.time();rng=random.Random(316251);rr=np.random.default_rng(316251);groups={};totals=[];maxstat={};first=[]
 def test(s,group,expect=None,mask=None,sign=None):
  n,d,stat,choices=decode(s,True);e=errors(n,d);assert D.moments(e)==list(map(int,s))
  if expect is not None:assert e==expect
  if mask is None:mask=rr.integers(0,4096,4095,dtype=np.int64);sign=phase(expect,mask) if expect is not None else phase(e,mask)
  assert phase(e,mask)==sign
  row=groups.setdefault(group,{'cases':0,'pivot_reordered':0,'min_weight':35,'max_weight':0,'max_heads':0,'max_skips':0,'phase_checks':0});row['cases']+=1;row['pivot_reordered']+=stat['skips']>0;row['min_weight']=min(row['min_weight'],len(e));row['max_weight']=max(row['max_weight'],len(e));row['max_heads']=max(row['max_heads'],len(choices));row['max_skips']=max(row['max_skips'],stat['skips']);row['phase_checks']+=1
  for k,v in stat.items():maxstat[k]=max(v,maxstat.get(k,0))
  totals.append(stat)
  if stat['skips'] and len(first)<10:first.append({'weight':len(e),'skips':stat['skips'],'choices':choices})
 for w in range(36):
  for _ in range(8):
   E={x:rng.randrange(1,4096)for x in rng.sample(range(1,4096),w)};test(D.moments(E),'stratified',E)
 for kind,E in D.cases():
  if kind!='stratified':test(D.moments(E),kind,E)
 def force(w,N):
  xs=rng.sample(range(1,F),w);d=D.locator_of(xs);E={}
  for x in xs:
   a=D.ev(N,x);z=m(m(x,D.ev(U,x)),D.ev(D.divrem(d,[x,1])[0],x));assert a and z
   E[x]=D.div(a,z)
  return E
 for k in ORDER:
  for w in (3,17,35):
   for _ in range(4):
    E=force(w,D.g(k));test(D.moments(E),'new_U_forced_pole',E)
 for _ in range(32):
  E=force(35,D.G);n,d,stats,choices=decode(D.moments(E),True);assert choices[0]==K and stats['skips']>=17
  test(D.moments(E),'all_17_repeated_nodes_poles',E)
 for path in sys.argv[1:]:
  f=pathlib.Path(path)
  if f.suffix=='.json':
   obj=json.load(f.open());obj=obj['errors']if isinstance(obj,dict)else obj
   for E in obj:
    E={int(x):a for x,a in E.items()};test(D.moments(E),f.name,E)
  else:
   a=np.load(f);S=a['S'];M=a['M'] if 'M' in a else None;P=a['expected']if 'expected'in a else None
   for j,s in enumerate(S):
    if M is None or P is None:
     _,_,_,_,E=D.forward_checked(list(map(int,s)));test(s,f.name,E)
    else:test(s,f.name,mask=M[j],sign=int(P[j]))
 print(groups,flush=True);rank=linear_rank();assert rank==70
 out={'scope':'full classical mathematical decoder from original 70 moments; no physical DQI KMB or cost proof', 'rank_initial_GF4096':rank,'rank_initial_GF2':12*rank,'slots':SLOTS,'groups':groups,'total':len(totals),'all_syndrome_restoration_and_phase_checks':len(totals),'max_stats':maxstat,'mean_stats':{k:sum(a[k]for a in totals)/len(totals)for k in maxstat},'examples_reordered':first,'seconds':round(time.time()-start,3)}
 pathlib.Path('adaptive_cf_receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
