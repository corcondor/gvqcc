"""Known successful permutation-frame reuse; no candidate search."""
from portfolio import *
D=H/'terminal_frame'
SRC=H/'chart_transfer/candidate_NOT_SUBMIT.kmb'
PARENT='7be22729aae992f2f3fa408eba736300cf8cacc92ed5475e2a9707950cb153ff'
def main():
 assert digest(SRC)==PARENT
 K=NativeKMB.read(SRC);O=K.ops.copy();a,z=25678,25692
 f=list(range(37))
 for o in O[a:z]:
  assert o.raw==34
  i,j=o.wires;f[i],f[j]=f[j],f[i]
 suffix=[Op(o.raw,tuple(f[q]for q in o.wires),o.measurement,o.condition)for o in O[z:]]
 g=f.copy();rest=[]
 for i in range(22):
  if g[i]!=i:
   j=g.index(i);rest.append(Op(34,(g[i],i)));g[i],g[j]=g[j],g[i]
 assert g[:22]==list(range(22)) and f[36]==g[36]==36
 K.ops=O[:a]+suffix+rest;raw=K.to_bytes();hh=list(HEADER.unpack_from(raw,16));hh[5]=sum(len(o.wires)==3 for o in K.ops)
 dest=D/'candidate_NOT_SUBMIT.kmb';dest.write_bytes(raw[:16]+HEADER.pack(*hh)+raw[16+HEADER.size:]);L=NativeKMB.read(dest);P=L.ops
 assert P==K.ops and [(k,v)for k,v in K.sections if k>9]==[(k,v)for k,v in L.sections if k>9]
 b=BDD(NLEGAL);s0=[b.leaf(mask(i,NLEGAL))for i in range(22)]+[b.zero]*15;m=Machine(b,s0);cost=Fraction(0);t=time.time()
 @lru_cache(None)
 def prob(v):return Fraction(v.value.bit_count(),NLEGAL)if v.var<0 else (prob(v.low)+prob(v.high))/2
 def cc(m,o):
  if o.raw&127 not in (48,49,50):return Fraction(0)
  v=prob(b.and_(m.active,m.c.get(o.condition,b.zero))if o.raw&128 else m.active);prob.cache_clear();return v
 for o in O[:a]:
  cost+=cc(m,o);m.step(o,b.variable()if o.raw&127==80 else None);m.p=b.zero;m.rot=[]
 assert m.active is b.one and not m.stack,'restore under guard'
 n=Machine(b,m.s,m.c);n.active=m.active;n.stack=list(m.stack)
 for o in O[a:z]:m.step(o)
 assert all(m.s[j]is n.s[f[j]]for j in range(37))
 print('prefix and frame PASS',time.time()-t,flush=True)
 for i,(o,p)in enumerate(zip(O[z:],P[a:a+len(suffix)])):
  v=cc(m,o);assert v==cc(n,p);cost+=v
  event=b.variable()if o.raw&127==80 else None;m.step(o,event);n.step(p,event)
  assert all(m.s[j]is n.s[f[j]]for j in range(37)),('data',i)
  assert m.c==n.c and m.active is n.active and m.stack==n.stack,('classical',i)
  assert m.p is n.p and m.rot==n.rot,('phase/rot',i)
  m.p=n.p=b.zero;m.rot=[];n.rot=[]
 assert m.s==s0 and not m.stack and m.active is b.one
 for o in P[a+len(suffix):]:n.step(o)
 assert n.s==s0 and n.c==m.c and not n.stack and n.active is b.one and n.p is b.zero and not n.rot
 assert cost==Fraction(26687,16)
 receipt=dict(parent_sha256=PARENT,sha256=digest(dest),old_restore=[a,z],old_swaps=ser(O[a:z]),terminal_restore=ser(rest),frame=f,final_frame=g,ops_before=len(O),ops_after=len(P),static_before=paid(O),static_after=paid(P),expected_paid_before=float(cost),expected_paid_after=float(cost),all_legal_inputs=NLEGAL,independent_hmr=b.nvar,paired_suffix_comparisons=len(suffix),shared_prefix_ops=a,phase_classical_rotation_data='PASS',verification='PASS',seconds=time.time()-t,peakQ=37,official_KickMix=False,score_update=False,new_search=False)
 (D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print({k:v for k,v in receipt.items()if k not in ('old_swaps','terminal_restore','frame','final_frame')},flush=True)
if __name__=='__main__':main()
