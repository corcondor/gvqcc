from pathlib import Path
p=Path('recurrence_guard.py');s=p.read_text()
s=s.replace('cost=min(len(pairs),len(A)+d1-d0)','cost=min(len(pairs),len(A)+d1-d0,len(A)+len(B)-1,len(B)+d1-d0)')
a=s.index(' def cross(A,B,d0,d1,pairs):');z=s.index(' def zero_residual():',a)
s=s[:a]+''' def cross(A,B,d0,d1,pairs):
  C=Q[d0-1:d1];V=[S[j] for j in A];T=[S[i] for i in B];na,nb,nc=len(A),len(B),len(C)
  assert d0==B[0]-A[-1]
  n,orientation=min([(na+nc-1,'AC'),(na+nb-1,'AB'),(nb+nc-1,'BC')])
  if mode=='direct' or n>=len(pairs):
   stats['direct_blocks']+=1
   for i,j,d in pairs:product(Q[d-1],S[j],S[i])
   return
  stats['interpolated_blocks']+=1
  stats[orientation]=stats.get(orientation,0)+1
  terms=[]
  for x,row in enumerate(lagrange(n)):
   if orientation=='AC':
    a=powers(x,na);c=powers(x,nc);out=[row[i+na-1] if i+na-1<n else 0 for i in range(nb)]
   elif orientation=='AB':
    a=powers(x,na)[::-1];out=powers(x,nb);c=[row[i] if i<n else 0 for i in range(nc)]
   else:
    c=powers(x,nc);out=powers(x,nb)[::-1];a=[row[na+nb-2-j] if na+nb-2-j<n else 0 for j in range(na)]
   if any(a) and any(c) and any(out):terms.append((a,c,out))
  for i in range(nb):
   for j in range(na):
    for k in range(nc):
     actual=0
     for a,c,out in terms:actual^=D.mul(D.mul(a[j],c[k]),out[i])
     assert actual==int(i+na-1-j==k)
  stats['tensor_checks']=stats.get('tensor_checks',0)+na*nb*nc
  class Frame:
   def __init__(self,regs,output=False):self.regs=regs;self.output=output;self.p=None;self.row=None
   def add(self,k,p,j):
    if k:lin(k,self.regs[p if self.output else j],self.regs[j if self.output else p])
   def switch(self,row):
    p=None if row is None else next(j for j,c in enumerate(row) if c)
    w=None if row is None else [D.div(c,row[p]) for c in row]
    if self.p is not None:
     if p==self.p:
      for j in range(len(w)):
       if j!=p:self.add(w[j]^self.row[j],p,j)
      self.row=w;return self.regs[p],row[p]
     for j in range(len(self.row)):
      if j!=self.p:self.add(self.row[j],self.p,j)
    if p is not None:
     for j in range(len(w)):
      if j!=p:self.add(w[j],p,j)
    self.p,self.row=p,w
    return (self.regs[p],row[p]) if p is not None else (None,None)
  fa,fc,fo=Frame(V),Frame(C),Frame(T,True)
  for a,c,out in terms:
   x,u=fa.switch(a);y,v=fc.switch(c);w,t=fo.switch(out);coef=D.mul(D.mul(u,v),t)
   if coef!=1:scale(coef,x)
   product(x,y,w)
   if coef!=1:scale(coef,x,True)
  fa.switch(None);fc.switch(None);fo.switch(None)
'''+s[z:]
s=s.replace("for mode in ('direct','interpolate','joint'):","for mode in ('joint',):").replace("name=mode+('_prefix' if forward else '_guard')","name='transpose'+('_prefix' if forward else '_guard')").replace("'guard_receipt.json'","'transpose_receipt.json'")
Path('transpose_guard.py').write_text(s)
