#!/usr/bin/env python3
"""Independently verify the quadratic-retirement impossibility witnesses.
Uses uint8 arrays over only certificate inputs, independent of the packed-int
GF(2) elimination used by the search. No native verifier or quantum claim is
made for any approximate phase probe.
"""
import hashlib,json,pathlib,re
import numpy as np
base=pathlib.Path('gvqcc_repo')
report=json.loads((base/'invsqrt_rearchitecture_retire_results.json').read_text())
s=(base/'invsqrt_structural_e46.kmx').read_text().splitlines()
allxs=sorted({x for r in report['records'] for x in r['certificate']['input_rows']})
assert all(1<=x<=3133452 for x in allxs)
xs=np.array(allxs,dtype=np.uint32);index={x:i for i,x in enumerate(allxs)}
q=np.zeros((46,len(xs)),dtype=np.uint8)
for i in range(22):q[i]=(xs>>i)&1
conditional=0
for lineno,line in enumerate(s[:report['entry_before_line']-1],1):
 w=line.split();op=w[0];qs=[int(v) for v in re.findall(r'\bq(\d+)\b',line)]
 if op=='PUSH_CONDITION':conditional+=1;continue
 if op=='POP_CONDITION':conditional-=1;continue
 assert not conditional or op in ('Z','CZ','CCZ','NEG'),(lineno,line)
 if 'if' in w:assert op in ('Z','CZ','CCZ','NEG'),(lineno,line)
 if op=='X':q[qs[0]]^=1
 elif op=='CX':q[qs[1]]^=q[qs[0]]
 elif op=='CCX':q[qs[2]]^=q[qs[0]]&q[qs[1]]
 elif op=='SWAP':q[qs]=q[qs[::-1]]
 elif op=='CSWAP':
  c,a,b=qs;d=q[c]&(q[a]^q[b]);q[a]^=d;q[b]^=d
 elif op=='HMR':q[qs[0]]=0
 elif op in ('Z','CZ','CCZ','NEG','Z_POW','BIT_STORE0','BIT_INVERT','APPEND_TO_REGISTER','REGISTER'):pass
 else:raise ValueError((lineno,line))
rows=[]
for r in report['records']:
 ids=[index[x] for x in r['certificate']['input_rows']]
 a=q[:,ids];es=r['eligible'];assert len(ids)%2==0
 assert all(not int(np.bitwise_xor.reduce(a[i])) for i in es)
 assert all(not int(np.bitwise_xor.reduce(a[i]&a[j])) for at,i in enumerate(es) for j in es[at+1:])
 assert int(np.bitwise_xor.reduce(a[r['target']]))==1
 window=s[report['entry_before_line']-1:report['absent_from_phase_until_line']]
 assert all(f'q{r["target"]}' not in line.split() for line in window)
 rows.append({'target':r['target'],'excluded':r['excluded'],'witness_count':len(ids),'verified_inconsistent_constant_linear_quadratic_system':True})
out={'baseline_kmx_sha256':hashlib.sha256((base/'invsqrt_structural_e46.kmx').read_bytes()).hexdigest(),'independent_implementation':'NumPy uint8 gate simulator on witness inputs','unique_legal_inputs':len(xs),'records':rows,'status':'PASS'}
(base/'invsqrt_rearchitecture_retire_audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
