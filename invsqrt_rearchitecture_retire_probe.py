#!/usr/bin/env python3
"""Exact quadratic reconstruction of remainder bits absent from phase cone.
This explores a different optimization to gatewise affine contractions:
measurement-retire a complete value across the phase endpoint and rebuild it.
"""
import numpy as np,re,json,time,pathlib,random,hashlib
N=3133452;mask=((1<<(N+1))-1)^1
xs=np.arange(N+1,dtype=np.uint32)
q=[int.from_bytes(np.packbits(((xs>>i)&1).astype(np.uint8),bitorder='little').tobytes(),'little')&mask for i in range(22)]+[0]*24
del xs
s=pathlib.Path('gvqcc_repo/invsqrt_structural_e46.kmx').read_text().splitlines()
for line in s[:7572]:
 w=line.split();op=w[0];qs=list(map(int,re.findall(r'\bq(\d+)\b',line)))
 if op=='X':q[qs[0]]^=mask
 elif op=='CX':q[qs[1]]^=q[qs[0]]
 elif op=='CCX':q[qs[2]]^=q[qs[0]]&q[qs[1]]
 elif op=='CSWAP':
  c,a,b=qs;d=q[c]&(q[a]^q[b]);q[a]^=d;q[b]^=d
 elif op=='SWAP':a,b=qs;q[a],q[b]=q[b],q[a]
 elif op=='HMR':q[qs[0]]=0
 elif op in ('PUSH_CONDITION','POP_CONDITION','Z','CZ','CCZ','NEG','BIT_STORE0','BIT_INVERT','Z_POW','APPEND_TO_REGISTER','REGISTER'):pass
 else:raise ValueError(line)
pathlib.Path('invsqrt_rearchitecture_phase_work/entry_states.u64').write_bytes(b''.join(v.to_bytes((N+8)//8,'little') for v in q))
rng=random.Random(48);sample=[1,2,3,N]+[rng.randrange(1,N+1) for _ in range(508)]

def solve(target,excluded=()):
 eligible=[i for i in range(46) if i!=target and i not in excluded and q[i]]
 vals=[mask]+[q[i] for i in eligible]+[q[a]&q[b] for ia,a in enumerate(eligible) for b in eligible[ia+1:]]
 terms=[[]]+[[i] for i in eligible]+[[a,b] for ia,a in enumerate(eligible) for b in eligible[ia+1:]]
 qsg={i:sum(((q[i]>>x)&1)<<j for j,x in enumerate(sample)) for i in eligible}
 sigs=[(1<<len(sample))-1]+[qsg[i] for i in eligible]+[qsg[a]&qsg[b] for ia,a in enumerate(eligible) for b in eligible[ia+1:]]
 ts=sum(((q[target]>>x)&1)<<j for j,x in enumerate(sample));width=len(sample);row_inputs=list(sample)
 for it in range(len(vals)+2):
  bas={}
  for i,sv in enumerate(sigs):
   coeff=1<<i
   while sv:
    pivot=sv.bit_length()-1
    if pivot not in bas:bas[pivot]=(sv,coeff);break
    sv^=bas[pivot][0];coeff^=bas[pivot][1]
  tv=ts;sol=0
  while tv:
   p=tv.bit_length()-1
   if p not in bas:
    dual=1<<p
    for pivot in sorted(bas):
     if (bas[pivot][0]&dual).bit_count()&1:dual^=1<<pivot
    assert all(not((sv&dual).bit_count()&1) for sv in sigs)
    assert (ts&dual).bit_count()&1
    witness_rows=[row_inputs[j] for j in range(width) if dual>>j&1]
    return {'target':target,'excluded':list(excluded),'eligible':eligible,'exact_quadratic':False,'sample_rows':width,'feature_rank':len(bas),'refinements':it,'certificate':{'identity':'XOR of all quadratic feature rows is zero, XOR target is one','input_rows':witness_rows,'feature_xor_zero':True,'target_xor_one':True}}
   tv^=bas[p][0];sol^=bas[p][1]
  result=0;chosen=[]
  for i,v in enumerate(vals):
   if sol>>i&1:result^=v;chosen.append(terms[i])
  dif=result^q[target]
  if not dif:
   # Alternating matrix rank gives rank/2 minimal products for quadratic part.
   rows=[0]*46
   for a in chosen:
    if len(a)==2:u,v=a;rows[u]^=1<<v;rows[v]^=1<<u
   rb={}
   for v in rows:
    while v:
     p=v.bit_length()-1
     if p not in rb:rb[p]=v;break
     v^=rb[p]
   return {'target':target,'excluded':list(excluded),'eligible':eligible,'exact_quadratic':True,'terms':chosen,'rebuild_min_and_rank_bound':len(rb)//2,'sample_rows':width,'feature_rank':len(bas),'refinements':it,'checked_inputs':N}
  x=(dif&-dif).bit_length()-1
  block=min(256,N+1-x); lowmask=(1<<(x+block))-1;row_inputs.extend(range(x,x+block))
  sigs=[sv|((((v&lowmask)>>x))<<width) for sv,v in zip(sigs,vals)];ts|=(((q[target]&lowmask)>>x))<<width;width+=block
  if it%40==0:print('target',target,'refinement',it,'witness',x,flush=True)
start=time.monotonic();results=[]
for target,excluded in [(42,(21,)),(45,(21,)),(42,(45,21)),(45,(42,21))]:
 r=solve(target,excluded);results.append(r);print(json.dumps({k:v for k,v in r.items() if k!='certificate'}),flush=True)
 pathlib.Path('gvqcc_repo/invsqrt_rearchitecture_retire_results.json').write_text(json.dumps({'source':'e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6','entry_before_line':7573,'absent_from_phase_until_line':8567,'scope':'full-domain reconstruction of values only; native emitter not built','records':results,'elapsed_seconds':time.monotonic()-start,'refinement_block_rows':256},indent=2))
