#!/usr/bin/env python3
"""Global B/R address relabelings of FeMoCo: exact physical invariances,
not local angle edits. Large (1219x75) angle table changes are evaluated
for binary tensor proxy before the expensive REAL-KMB step.
"""
from pathlib import Path
import argparse,hashlib,json,time,sys
import numpy as np
from longtrain.physical_verify import Physical,decode
from givens_gauge_global import proxy

def permutation(B,kind,seed):
 rng=np.random.default_rng(seed)
 arr=np.arange(B)
 if kind=='reverse':return arr[::-1]
 if kind=='bit_reverse':
  assert B==127
  key=np.array([int(f'{i:07b}'[::-1],2) for i in arr])
  return np.argsort(key)
 if kind=='gray_order':return np.argsort(arr^(arr>>1))
 if kind=='bit_rotate':
  assert B==127
  key=((arr<<1)|(arr>>6))&127; return np.argsort(key)
 if kind=='shift':return np.roll(arr,int(seed%B))
 if kind=='blockreverse':return np.concatenate([arr[i:i+16][::-1] for i in range(0,B,16)])
 if kind=='block_shuffle':
  chunks=[arr[i:i+16] for i in range(0,B,16)];keys=rng.permutation(len(chunks));return np.concatenate([chunks[i] for i in keys])
 if kind=='random':return rng.permutation(B)
 if kind=='xorthree':
  assert B==127
  a,b,c=rng.choice(7,size=3,replace=False)
  key=arr^(( ((arr>>b)^(arr>>c))&1 )<<a)
  assert len(np.unique(key))==B
  return np.argsort(key)
 raise ValueError(kind)

def transform(d,kind,seed,perm_r=False):
 result={k:np.array(v) for k,v in d.items()}
 R,B,C=d['W'].shape;N=76;rows=d['angle_words'];W=d['W'];U=d['U'];H=d['H2_I']
 rng=np.random.default_rng(seed)
 order_r=rng.permutation(R) if perm_r else np.arange(R)
 if kind=='one_global':
  pv=permutation(B,'xorthree',seed)
  orders=np.stack([pv]*R)
 elif kind=='cyclic_all':
  orders=np.stack([permutation(B,'shift',seed+r*17) for r in range(R)])
 elif kind=='by_norm':
  orders=np.stack([np.argsort(-np.linalg.norm(W[r],axis=1)) for r in range(R)])
 elif kind=='by_lex_angle':
  orders=np.stack([np.lexsort(rows[N+r*B:N+(r+1)*B,:12].T) for r in range(R)])
 elif kind=='block_matrix':
  orders=np.stack([permutation(B,'block_shuffle',seed+r) for r in range(R)])
 else:
  orders=np.stack([permutation(B,kind,seed+r if kind in {'xorthree','random','shift'} else seed) for r in range(R)])
 seq=np.concatenate([N+order_r[r]*B+orders[order_r[r]] for r in range(R)])
 newangle=np.vstack([rows[:N],rows[seq]])
 result['angle_words']=newangle
 result['U']=np.array([U[order_r[r]][orders[order_r[r]]] for r in range(R)])
 result['W']=np.array([W[order_r[r]][orders[order_r[r]]] for r in range(R)])
 result['H2_I']=H[order_r]
 return result,{'r_order':order_r.tolist(),'b_orders_sha256':hashlib.sha256(orders.tobytes()).hexdigest(),'b_orders_first_r':orders[0,:25].tolist(),'num_angle_changed':int(np.count_nonzero(newangle!=rows))}

def main():
 a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--data',required=True);a.add_argument('--out',required=True);a.add_argument('--trials',type=int,default=90);args=a.parse_args()
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 with np.load(args.source) as z: d={k:np.array(z[k]) for k in z.files}
 phys=Physical(args.data);bm=phys.evaluate(d);bp=proxy(d['angle_words'].astype(np.uint8))
 names=['one_global','cyclic_all','by_norm','by_lex_angle','block_matrix','reverse','bit_reverse','gray_order','bit_rotate','shift','blockreverse','block_shuffle','random','xorthree']
 results=[]
 for trial in range(args.trials):
  kind=names[trial%len(names)];seed=trial*11+27;perm_r=trial%3==0
  transformed,detail=transform(d,kind,seed,perm_r)
  ranks=proxy(transformed['angle_words'].astype(np.uint8));rec={'pattern':kind,'trial':trial,'seed':seed,'perm_r':perm_r,'proxy':sum(ranks),'proxy_delta':sum(ranks)-sum(bp),'proxy_perbank':ranks,**detail}
  results.append(rec)
  if trial%10==0:print('trial',trial,kind,'proxy',rec['proxy'],'baseline',sum(bp),flush=True)
 results.sort(key=lambda x:x['proxy']);best=[]
 for r in results[:6]:
  tr,details=transform(d,r['pattern'],r['seed'],r['perm_r'])
  phy=phys.evaluate(tr)
  for key in ['lambda_eff','error_1','error_2','E_gap']:
   if abs(phy[key]-bm[key])>5e-7:raise AssertionError((key,phy[key],bm[key],r))
  dest=out/f"bperm_{r['trial']:03}_{r['pattern']}.npz";np.savez_compressed(dest,**tr)
  r['file']=dest.name;r['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();r['physical']=phy
  best.append(r)
 res={'source':args.source,'source_sha256':hashlib.sha256(Path(args.source).read_bytes()).hexdigest(),'base_phys':bm,'base_proxy':sum(bp),'all_trials':results,'selected_exact_physics':best,'no_native_KickMix':True}
 (out/'reindex_results.json').write_text(json.dumps(res,indent=2)+'\n')
 print('BEST',[(r['pattern'],r['proxy'],r['num_angle_changed']) for r in best],flush=True)
if __name__=='__main__':main()