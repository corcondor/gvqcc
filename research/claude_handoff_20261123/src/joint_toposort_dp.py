#!/usr/bin/env python3
"""Nonlocal Givens topological schedule + exact per-address 74-bit sign gauge DP.
Both transformations preserve the decoded vectors; test all 1219 rows.
"""
import argparse,hashlib,json,time,sys
from pathlib import Path
import numpy as np
from longtrain.physical_verify import decode,Physical
from givens_gauge_tree_dp import solve
from givens_gauge_global import proxy

def order(edges,rng,temp,priority=None):
 pred=[set(i for i in range(j) if len(set(edges[i])&set(edges[j]))>0) for j in range(len(edges))]
 remain=set(range(len(edges)));done=set();p=[]
 while remain:
  ready=np.array(sorted(j for j in remain if pred[j]<=done),dtype=np.int32)
  if priority is not None:
   vals=priority[ready].astype(float)
   idx=ready[np.argmin(vals+rng.normal(size=len(vals))*temp)]
  elif temp==0:idx=ready[0]
  elif temp==999:idx=rng.choice(ready)
  else:
   w=np.exp(-(ready-ready.min())/temp);w=w/w.sum();idx=rng.choice(ready,p=w)
  idx=int(idx);p.append(idx);remain.remove(idx);done.add(idx)
 return p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--trials',type=int,default=64);a=ap.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with np.load(a.source) as z:d={k:np.array(z[k]) for k in z.files}
 original=d['angle_words'].astype(np.uint8);E=d['tree_edges'];v0=decode(original,E)
 rng=np.random.default_rng(4433);results=[]
 modes=['bitplane_6','affine_4','min_value','bank_weighted']
 for t in range(a.trials):
  temp=[0,0.6,1.5,4,12,999][t%6]
  perm=order(E,rng,temp);w=original[:,perm];ed=E[perm];mode=modes[t%4]
  gauge,obj=solve(w,ed,mode);ps=proxy(gauge);rank=sum(ps)
  rec=dict(trial=t,temp=temp,mode=mode,perm=perm,angle_changed=int(np.count_nonzero(gauge!=original)),proxy_rank_sum=rank,proxy_by_bank=ps)
  results.append(rec)
  if t%10==0: print('trial',t,'mode',mode,'temp',temp,'rank',rank,flush=True)
 results.sort(key=lambda r:r['proxy_rank_sum'])
 P=Physical(a.data);b=P.evaluate(d)
 for r in results[:5]:
  cand=dict(d)
  cand['tree_edges']=E[r['perm']]
  cand['angle_words']=solve(original[:,r['perm']],cand['tree_edges'],r['mode'])[0].astype(np.int64)
  maxdiff=float(np.max(np.abs(v0-decode(cand['angle_words'],cand['tree_edges']))))
  assert maxdiff<1e-13
  phy=P.evaluate(cand)
  assert abs(phy['lambda_eff']-b['lambda_eff'])<1e-8 and abs(phy['error_2']-b['error_2'])<1e-7
  fp=out/f"joint_{r['trial']:02}.npz";np.savez_compressed(fp,**cand)
  r.update(max_abs_decode_diff=maxdiff,physics=phy,file=fp.name,sha256=hashlib.sha256(fp.read_bytes()).hexdigest())
 (out/'joint_toposort_results.json').write_text(json.dumps({'source':a.source,'trials':results,'base_rank':sum(proxy(original)),'base_physics':b,'official_KickMix_verified':False},indent=2)+'\n')
 print('BEST',[(r['trial'],r['proxy_rank_sum'],r['mode'],r['temp']) for r in results[:5]],flush=True)
if __name__=='__main__':main()