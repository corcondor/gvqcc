"""Phase-ledger-aware nonlinear chart transport across V4 fallback gaps.
Place in central/global_chart of the V4 reproducibility bundle.
Run this, then python verify_portfolio.py v5virtual.
"""
import propagated_chart as pc
from propagated_chart import *
from functools import lru_cache

def main():
 rows=pickle.loads((P/'exact_rows.pkl').read_bytes());raw=pickle.loads((P/'portfolio_v4context_300_path_unmapped.pkl').read_bytes());phase=phaseonly();ledger=json.loads((P/'global_phase_anf.json').read_text());ban=set(ledger['phase_dependent_hmr_ops']+ledger['rotation_dependent_hmr_ops']);allowed=set(phase)-ban
 original_gate=pc.gate;index={id(o):i for i,o in enumerate(OPS)}
 def gate(o,d,ps,nps,guarded):
  if o.raw==80 and d==o.wires[0] and not guarded and index[id(o)] in allowed:
   return d,[Op(64,(),measurement=o.measurement)]
  return original_gate(o,d,ps,nps,guarded)
 pc.gate=gate
 oldswitch=pc.bestswitch
 @lru_cache(8192)
 def sw(ps,d,e):return oldswitch(ps,d,e)
 pc.bestswitch=lambda ps,d,e:sw(frozenset(ps),d,e)
 gg=[(a,z,e,f) for a,z,e,f in fallback_gaps(raw) if e is not None and f is not None and any(k in allowed for k in range(a,z))]
 constructed=[];tested=0;t=time.time()
 for a,z,e,f in sorted(gg,key=lambda g:g[1]-g[0],reverse=True):
  tested+=1;g=pc.build(a,z,e,f,rows);sw.cache_clear()
  if g is None:continue
  m=[(k,OPS[k].measurement) for k in range(a,z)if OPS[k].raw&127==80]
  mm=[o.measurement for o in g if o.raw&127==80]
  if len(set(m0 for k,m0 in m))!=len(m):continue
  removed=[k for k,m0 in m if m0 not in mm]
  if not removed or any(k not in allowed for k in removed):continue
  if any(36 in o.wires for o in g):continue
  meta={'removed_hmrs':removed,'paid_delta':stats(g)['paid']-stats(OPS[a:z])['paid'],'virtual_hmr':True}
  constructed.append(('ripple',a,z,e,f,getrel(rows[a],e),getrel(rows[z],f),g,meta))
  print('constructed',a,z,meta,flush=True)
 by={e[1]:e for e in constructed};new=[];i=0
 while i<len(raw):
  r=raw[i];a=r[1]
  if a not in by:new.append(r);i+=1;continue
  e=by[a];new.append(e);z=e[2]
  while i<len(raw) and raw[i][1]<z:assert raw[i][0]=='fallback';i+=1
  assert i==len(raw) or raw[i][1]==z
 (P/'v5_virtual_hmr_screen.json').write_text(json.dumps({'tested':tested,'eligible_gaps':len(gg),'constructed':[dict(start=e[1],end=e[2],**e[8])for e in constructed],'source_ops':sum(e[2]-e[1]for e in constructed),'seconds':time.time()-t,'official_verifier':False},indent=2))
 if constructed:(P/'portfolio_v5virtual_path_unmapped.pkl').write_bytes(pickle.dumps(new))
if __name__=='__main__':main()
