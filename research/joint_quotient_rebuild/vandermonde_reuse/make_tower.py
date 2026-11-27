from pathlib import Path
s=Path('transpose_guard.py').read_text()
s=s.replace('import direct_codec as D','import direct_codec as D\nimport os\nsys.modules["circ"]=km\nsys.path.insert(0,os.environ["GVQCC_TENSOR64_DIR"])\nimport tensor64 as H\nassert H.ar.field(12).modulus==0x1053')
loc=s.index('@functools.cache\ndef schedule_dp')
s=s[:loc]+'''@functools.cache
def tower_cost(na,nb,nc):
 if min(na,nb)<2:return 10**9
 mod,w,dec=H.thickening(nc)
 ld=max((v.bit_length()-1)//6 for v in w[:12*na] if v)
 rd=max((v.bit_length()-1)//6 for v in w[:12*nb] if v)
 n=ld+rd+1
 return 15*n if n<=64 else 10**9
@functools.cache
def transpose_tower(na,nb,nc):
 pair,unpair=H.trace_pairing()
 def reverse(v,n):return sum(((v>>(12*i))&4095)<<(12*(n-1-i)) for i in range(n))
 def linear(v,n,columns):return sum(H.ar.apply(columns,(v>>(12*i))&4095)<<(12*i) for i in range(n))
 terms=[]
 for a,b,w in H.two_sided(nc,na,nb):
  terms.append((reverse(a,na),linear(w,nc,pair),linear(b,nb,unpair)))
 # Check the entire binary tensor; not a sampled field-multiplication test.
 for i in range(12*na):
  result=[0]*(12*nc)
  for a,c,o in terms:
   if a>>i&1:
    for j in H.ar.bits(c):result[j]^=o
  for j,value in enumerate(result):
   d=j//12+i//12-na+1
   expected=(D.mul(1<<(i%12),1<<(j%12))<<(12*d)) if 0<=d<nb else 0
   assert value==expected,(na,nb,nc,i,j,value,expected)
 return terms
'''+s[loc:]
s=s.replace('cost=min(len(pairs),len(A)+d1-d0,len(A)+len(B)-1,len(B)+d1-d0)','cost=min(42*min(len(pairs),len(A)+d1-d0,len(A)+len(B)-1,len(B)+d1-d0),tower_cost(len(A),len(B),d1-d0+1))')
anchor="  if mode=='direct' or n>=len(pairs):"
insert='''  tc=tower_cost(na,nb,nc)
  if mode=='joint' and tc<42*min(n,len(pairs)):
   terms=transpose_tower(na,nb,nc);assert len(terms)<=tc
   stats['tower_blocks']=stats.get('tower_blocks',0)+1
   stats['tower_ccx']=stats.get('tower_ccx',0)+len(terms)
   stats['tower_basis_checks']=stats.get('tower_basis_checks',0)+144*na*nc
   x=[q for word in V for q in word];y=[q for word in C for q in word];z=[q for word in T for q in word]
   prev=[None,None,None]
   def switch(qs,mask,idx,out=False):
    ids=list(H.ar.bits(mask));p=ids[0];last=prev[idx]
    def edge(j,p):
     if out:b.cx(qs[p],qs[j])
     else:b.cx(qs[j],qs[p])
    if last is not None:
     lp,lm=last
     if lp==p:
      for j in H.ar.bits(lm^mask):
       assert j!=p;edge(j,p)
      prev[idx]=(p,mask);return qs[p]
     for j in H.ar.bits(lm^(1<<lp)):edge(j,lp)
    for j in ids[1:]:edge(j,p)
    prev[idx]=(p,mask);return qs[p]
   for am,cm,om in terms:
    xx=switch(x,am,0);yy=switch(y,cm,1);zz=switch(z,om,2,True);b.ccx(xx,yy,zz)
   for idx,qs in enumerate((x,y,z)):
    if prev[idx] is not None:
     p,m=prev[idx]
     for j in H.ar.bits(m^(1<<p)):
      if idx==2:b.cx(qs[p],qs[j])
      else:b.cx(qs[j],qs[p])
   return
'''
s=s.replace(anchor,insert+anchor)
a=s.index(' def zero_residual():');z=s.index(' for args in bs:',a)
s=s[:a]+''' def zero_residual():
  # PR215 temporary-AND ladder, PR93 central phase pool: reuse group work.
  x=[q for i in range(K,N) for q in S[i]];assert len(x)==420
  b.x(km.array(x));flags=b.alloc_qubits(24);groups=[x[(i*420)//24:((i+1)*420)//24] for i in range(24)]
  for i,g in enumerate(groups):b.multi_controlled_x(g,flags[i])
  b.multi_controlled_x(flags,target)
  for i,g in reversed(list(enumerate(groups))):
   mask=b.alloc_bits(1)[0];b.hmr(flags[i],mask);b.push_condition(mask)
   # Compute all but the last AND, use a conditional CZ instead of CCX.
   w=b.alloc_qubits(len(g)-2);b.init_and(g[0],g[1],w[0])
   for j in range(1,len(w)):b.init_and(w[j-1],g[j+1],w[j])
   b.cz(w[-1],g[-1]);
   for j in range(len(w)-1,0,-1):b.del_and(w[j-1],g[j+1],w[j])
   b.del_and(g[0],g[1],w[0]);b.free(w);b.pop_condition();b.free(mask)
  b.free(flags);b.x(km.array(x))
'''+s[z:]
s=s.replace("name='transpose'","name='tower'").replace("'transpose_receipt.json'","'tower_receipt.json'")
Path('tower_guard.py').write_text(s)
