"""Exact product search using the intersection of two restriction kernels.
C+E must be an independent basis, C contains 1, u in C.
"""
import argparse,json,time,sys
from pathlib import Path
from itertools import combinations

def basis(vs):
 p={};out=[]
 for v in vs:
  x=v
  while x:
   k=x.bit_length()-1
   if k in p:x^=p[k]
   else:p[k]=x;out.append(v);break
 return out

def lin(vs,c):
 z=0
 while c:
  j=(c&-c).bit_length()-1;z^=vs[j];c&=c-1
 return z

def ker_images(C,E,m):
 p={};n=len(C);K={0:0}
 for j,x in enumerate(C+E):
  x&=m;c=1<<j
  while x:
   k=x.bit_length()-1
   if k in p:y,t=p[k];x^=y;c^=t
   else:p[k]=(x,c);break
  if not x and j>=n:
   beta=c>>n
   for a,b in list(K.items()):K[a^beta]=b^c
 return K

def directions(C,E,u,one):
 A=ker_images(C,E,one^u);B=ker_images(C,E,u);ret={}
 for beta in (A.keys()&B.keys())-{0}:
  w=lin(C+E,A[beta]);v=lin(C,(A[beta]^B[beta])&((1<<len(C))-1))
  assert u&v==w and A[beta]>>len(C)==B[beta]>>len(C)==beta
  ret[beta]=(u,v,w)
 return ret

def replay(rows,ops,one):
 q=rows[:]
 for raw,ws,m,c in ops:
  k=raw&127
  if k==17:q[ws[0]]^=one
  elif k==33:q[ws[1]]^=q[ws[0]]
  elif k==34:q[ws[0]],q[ws[1]]=q[ws[1]],q[ws[0]]
  elif k==49:q[ws[2]]^=q[ws[0]]&q[ws[1]]
  elif k==80:q[ws[0]]=0
  elif k not in (0,16,32,48):raise ValueError(raw)
 return q

def main():
 p=argparse.ArgumentParser();p.add_argument('family',type=Path);p.add_argument('--vendor',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--bank',type=int,default=6);p.add_argument('--start',type=int,default=8991);p.add_argument('--end',type=int,default=9150);p.add_argument('--pairs',action='store_true');a=p.parse_args()
 sys.path.insert(0,str(a.vendor));import verify_native as V;import numpy as np
 start=time.time();c=V.parse(a.family/f'angle_k_{a.bank}.kmb');n=1219;one=(1<<(2*n))-1
 with np.load(a.family/'submission.npz') as d:t=V.targets(d['angle_words'])
 k=a.bank;s=[x|(y<<n) for x,y in zip(V.initial(c,t[k],n),V.initial(c,t[k+1],n))];before=replay(s,c['ops'][:a.start],one);after=replay(before,c['ops'][a.start:a.end+1],one)
 C=basis([one]+before);E=basis(C+after)[len(C):];assert len(E)<12
 P=[s[q] for q in c['registers']['selection']]
 candidates={lin(P,i) for i in range(1,1<<len(P))};candidates.update(before)
 if a.pairs:candidates.update(x^y for x,y in combinations(before,2))
 candidates={min(v,v^one) for v in candidates if v not in (0,one)}
 cp={}
 for v in C:
  while v:
   i=v.bit_length()-1
   if i in cp:v^=cp[i]
   else:cp[i]=v;break
 def member(v):
  while v:
   i=v.bit_length()-1
   if i not in cp:return False
   v^=cp[i]
  return True
 candidates=sorted(v for v in candidates if member(v));found={};num=0
 for u in candidates:
  z=directions(C,E,u,one);num+=bool(z)
  for k,v in z.items():found.setdefault(k,v)
 receipt={'sha256':c['sha256'],'npz_sha256':V.sha(a.family/'submission.npz'),'bank':a.bank,'start':a.start,'end':a.end,'rank_C':len(C),'rank_U_over_C':len(E),'candidate_factors':len(candidates),'factors_with_innovation':num,'quotient_directions':sorted(found),'witnesses':{str(k):[hex(t) for t in v] for k,v in found.items()},'seconds':round(time.time()-start,3),'scope':'both legal directions, all 1219 addresses each; enumerated left factors, exact right-factor search'}
 a.out.write_text(json.dumps(receipt,indent=2)+'\n');print({k:v for k,v in receipt.items() if k!='witnesses'},flush=True)
if __name__=='__main__':main()
