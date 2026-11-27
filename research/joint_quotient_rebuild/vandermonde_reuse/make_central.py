from pathlib import Path
s=Path('tower_guard.py').read_text()
loc=s.index('@functools.cache\ndef schedule_dp')
s=s[:loc]+'''@functools.cache
def central_order(na,nb,nc):
 terms=transpose_tower(na,nb,nc)
 # PR5 parity routing / PR93 centralized hub: terms in one cross block commute.
 # Minimize the sum of exact CX costs with retained pivot coordinates.
 counts=[{} for _ in range(3)]
 for t in terms:
  for k,m in enumerate(t):
   for j in H.ar.bits(m):counts[k][j]=counts[k].get(j,0)+1
 def pivot(m,k):return max(H.ar.bits(m),key=lambda j:(counts[k][j],-j))
 def route(start):
  todo=list(range(len(terms)));prev=[0]*3;p=[0]*3;seq=[];score=0
  while todo:
   if not seq and start is not None:i=start
   else:
    def cost(i):
     t=terms[i];c=0
     for k,m in enumerate(t):
      c+=(prev[k]^m).bit_count() if prev[k] and (m>>p[k]&1) else max(prev[k].bit_count()-1,0)+m.bit_count()-1
     return c,i
    i=min(todo,key=cost)
   t=terms[i];todo.remove(i);ps=[]
   for k,m in enumerate(t):
    if prev[k] and m>>p[k]&1:score+=(prev[k]^m).bit_count();ps.append(p[k])
    else:score+=max(prev[k].bit_count()-1,0)+m.bit_count()-1;ps.append(pivot(m,k))
   seq.append((t,tuple(ps)));prev=list(t);p=ps
  score+=sum(m.bit_count()-1 for m in prev)
  return score,seq
 return min((route(None),route(0),route(len(terms)-1)),key=lambda a:a[0])
'''+s[loc:]
s=s.replace("   terms=transpose_tower(na,nb,nc);assert len(terms)<=tc","   order_cost,ordered=central_order(na,nb,nc);terms=[t for t,p in ordered];assert len(terms)<=tc\n   stats['tower_CX']=stats.get('tower_CX',0)+order_cost")
s=s.replace('   def switch(qs,mask,idx,out=False):\n    ids=list(H.ar.bits(mask));p=ids[0];last=prev[idx]','   def switch(qs,mask,idx,p,out=False):\n    ids=list(H.ar.bits(mask));assert p in ids;last=prev[idx]')
s=s.replace('    for j in ids[1:]:edge(j,p)','    for j in ids:\n     if j!=p:edge(j,p)')
s=s.replace('   for am,cm,om in terms:\n    xx=switch(x,am,0);yy=switch(y,cm,1);zz=switch(z,om,2,True);b.ccx(xx,yy,zz)','   for (am,cm,om),(pa,pc,po) in ordered:\n    xx=switch(x,am,0,pa);yy=switch(y,cm,1,pc);zz=switch(z,om,2,po,True);b.ccx(xx,yy,zz)')
s=s.replace("name='tower'","name='central'").replace("'tower_receipt.json'","'central_receipt.json'")
Path('central_guard.py').write_text(s)
