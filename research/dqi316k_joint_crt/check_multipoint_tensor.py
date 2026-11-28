"""Exact coefficient tensor check, including overlapping input source sets.
Each evaluation/interpolation representation is checked at every basis pair.
No quantum inputs are used to construct the schedule.
"""
import json
from pathlib import Path
from multipoint_guard247 import P,C,eval_forms,points
seen=set();checked=0;maxn=0
for n in range(20,53):
 for d in (2,4,16):
  for lo,hi in P.plan(n,d)[1]:
   _,rr=P.block_cost(lo,hi,d)
   if rr is None:continue
   for ev,r,h0,h1,j0,j1,u0,u1 in rr:
    if not ev:continue
    key=(d,r,h0,h1,j0,j1,u0,u1)
    if key in seen:continue
    seen.add(key);forms=eval_forms(*key);maxn=max(maxn,len(forms))
    for t in range(u0,u1+1):
     for j in range(j0,j1+1):
      for h in range(h0,h1+1):
       z=C.xor_word(C.m(C.m(U.get(d*t+r,0),C.gf_pow(V.get(j,0),d,12,C.MOD)),W.get(d*h+r,0)) for U,V,W in forms)
       assert z==int(t+j==h), (key,t,j,h,z)
       checked+=1
out=dict(scope="exact GF4096 coefficients, not whole tape proof",distinct_chunks=len(seen),checks=checked,max_eval_points=maxn)
print(json.dumps(out),flush=True);Path("multipoint_tensor_receipt.json").write_text(json.dumps(out,indent=2))
