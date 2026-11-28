"""#298 + #297: shared guarded linear-form cache, at most six clean bits.
Fixed grouping depends ONLY on the rank-42 tensor, not on syndrome/measurement inputs.
The six scratch wires are clean after load_den and before clear_den.
No host-side data-dependent choice. The higher-confluent limitation is unchanged.
"""
from gauge_joint import *
import random
from collections import defaultdict

def partition(terms, maxrank=6):
    allm={a for a,b,z in terms}; best=None
    for seed in range(64):
        rng=random.Random(298202611+seed); left=set(allm); groups=[]
        while left:
            basis=[]; sp={0}
            while len(basis)<maxrank and left-sp:
                opts=sorted(left-sp); rng.shuffle(opts)
                v=max(opts,key=lambda x:len(left & (sp | {x^y for y in sp})))
                basis.append(v); sp |= {v^y for y in sp}
            cov=left & sp; groups.append((basis,cov)); left-=cov
        score=(sum(len(b) for b,_ in groups),len(groups))
        if best is None or score<best[0]:best=(score,groups)
    out=[]
    for basis,ms in best[1]:
        rep={0:0}
        for j,v in enumerate(basis):rep.update({a^v:c^(1<<j) for a,c in list(rep.items())})
        assert len(rep)==1<<len(basis)
        items=[(rep[a],b,z) for a,b,z in terms if a in ms]
        assert all(c and c<1<<len(basis) for c,b,z in items)
        out.append((tuple(basis),tuple(items)))
    assert sum(len(s) for b,s in out)==len(terms)
    return tuple(out)

GROUPS=partition(TERMS)
RANKSUM=sum(len(b) for b,t in GROUPS)
def certify():
    for i in range(12):
      for j in range(12):
       for flag in (0,1):
        val=0
        for basis,terms in GROUPS:
         bits=sum((flag*((a>>i)&1))<<k for k,a in enumerate(basis))
         for m,b,z in terms:
          if (bits&m).bit_count()%2 and b>>j&1:val^=z
        assert val==flag*mul(1<<i,1<<j)
    coeffs=0
    for basis,_ in GROUPS:
      for a in basis:
       for x in range(4096):
        for flag in (0,1):
         c=flag*((a&x).bit_count()%2)
         assert c^(flag*((a&x).bit_count()%2))==0
         coeffs+=1
    return {'bilinear_basis_guard_cases':288,'measurement_coefficients':coeffs,'rank_sum':RANKSUM,'groups':[(len(b),len(t)) for b,t in GROUPS]}

class SpanGauge(GaugeJoint):
 def cached(self,flag,x,jobs,scratch,repay=False):
  assert len(scratch)==6 and len(set(scratch))==6
  assert not set(scratch)&(set(x)|{flag})
  for y,t in jobs:
   assert not set(y)&set(x) and not set(y)&set(scratch)
   if not repay:assert not set(t)&(set(x)|set(y)|set(scratch)|{flag})
  for basis,terms in GROUPS:
   cache=scratch[:len(basis)]
   for m,h in zip(basis,cache):
    lo=len(self.ops);p=self.parity_frame(x,m);hi=len(self.ops)
    self.ccx(flag,p,h);self.rev(lo,hi)
   for c,b,z in terms:
    lo=len(self.ops);p=self.parity_frame(cache,c);hi=len(self.ops)
    for y,t in jobs:
     l=len(self.ops);q=self.parity_frame(y,b)
     if repay:
      h=len(self.ops)
      for j in range(12):
       if z>>j&1:self.cz(p,q,j)
      self.rev(l,h)
     else:
      outs=[t[i] for i in range(12) if z>>i&1];k=outs[0]
      for v in outs[1:]:self.cx(k,v)
      h=len(self.ops);self.ccx(p,q,k);self.rev(l,h)
    self.rev(lo,hi)
   for m,h in zip(basis,cache):
    self.hmr(h,72);lo=len(self.ops);p=self.parity_frame(x,m);hi=len(self.ops)
    self.cz(flag,p,72);self.bclear(72);self.rev(lo,hi)
 def gated_madd(self,flag,x,y,t,aux):
  self.cached(flag,x,[(y,t)],tuple(range(aux,aux+6)))
 def gated_repay(self,flag,x,y,aux):
  self.cached(flag,x,[(y,None)],tuple(range(aux,aux+6)),True)
 def update_source(self,A,B,ws,anchor,common):
  b,w=ws[:12],ws[12:24];sc=ws[32];n=len(A)-1
  self.madd(A[anchor],b,w);jobs=[]
  for i in range(1 if common else 2,n):
   if common and (i==1 or i==n-1):jobs.append((B[i+1],A[i]))
   else:self.madd(w,B[i+1],A[i])
  if jobs:self.cached(sc,w,jobs,ws[24:30])
  self.erase_product(A[anchor],b,w)
 def down_rhs(self,f,B,ws,anchor,common):
  b,w=ws[:12],ws[12:24];sc=ws[32];n=len(f)
  self.madd(f[anchor],b,w);jobs=[]
  for i in range(1 if common else 2,n):
   if common and (i==1 or i==n-1):jobs.append((B[i+1],f[i]))
   else:self.madd(w,B[i+1],f[i])
  if jobs:self.cached(sc,w,jobs,ws[24:30])
  self.erase_product(f[anchor],b,w)

def main():
 import gauge_joint as G
 cert=certify();print('exact tensor and cache certificate',cert,flush=True)
 old=G.GaugeJoint;G.GaugeJoint=SpanGauge
 try:q,m=G.make_gauge()
 finally:G.GaugeJoint=old
 print('new metrics',m['total'],flush=True)
 root=ROOT/'schur_connection';j=json.load(open(root/'core_shell.json'))
 panels={'captured':np.concatenate([a.native_rows(root/'shell_before.bin',j),a.native_rows(root/'forced_before.bin',j)]),'fresh':np.load('fresh_all_weights.npy'),'higher_confluent':np.load('higher_confluent_obstruction.npy')}
 res={}
 for k,rows in panels.items():
  s,p=q.evaluate(rows,2026113029);res[k]=solve_check(q,rows,s,p);print(k,res[k],flush=True)
  if k!='higher_confluent':assert not any(v for key,v in res[k].items() if key.endswith('indices'))
  else:assert not any(res[k][key] for key in ['source_error_indices','scratch_error_indices','phase_error_indices'])
 export(q,j,'span_gauge_physical.txt')
 receipt={'scope':'physical #298 converter (not a full oracle), fixed tensor-only cache groups','Q':900,'certificate':cert,'old':190110,'new':m['total']['ccx'],'metrics':m,'panels':res,'HMR':sum(g[0]=='HMR' for g in q.ops),'sha256':hashlib.file_digest(open('span_gauge_physical.txt','rb'),'sha256').hexdigest()}
 Path('span_gauge_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('COMPLETE',receipt['new'],flush=True)
if __name__=='__main__':main()
