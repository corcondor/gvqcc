"""Exact backward erasability closure C_(j+1)= C intersect Phi_2(C_j).
If the closure stops below C, no sequence of affine basis changes and HMRs
with immediate quadratic phase corrections can erase C to the protected F.
"""
from tail_hyperplane import *

def make_piv(rows):
 p={}
 for v in rows:
  while v:
   h=v.bit_length()-1
   if h in p:v^=p[h]
   else:p[h]=v;break
 return p

def reduce(p,v):
 while v:
  h=v.bit_length()-1
  if h not in p:return v
  v^=p[h]
 return 0

def full_reduce(p,v):
 for h,x in sorted(p.items(),reverse=True):
  if v>>h&1:v^=x
 return v

def grow(C,F,one):
 qrows=F+[a&b for i,a in enumerate(F)for b in F[i+1:]]
 p=make_piv(qrows)
 proj={};out=[]
 for v in C:
  # Need a linear projection, NOT leading-only reduction.
  r=full_reduce(p,v);c=v
  while r:
   h=r.bit_length()-1
   if h in proj:r^=proj[h][0];c^=proj[h][1]
   else:proj[h]=(r,c);break
  if not r and c:out.append(c)
 out=basis(F+out)
 return out,len(p)

def closure(C,F,one):
 ranks=[len(F)];quad=[];layers=[F[:]]
 while len(F)<len(C):
  G,r=grow(C,F,one);quad.append(r)
  if len(G)==len(F):break
  F=G;ranks.append(len(F));layers.append(F[:])
 return dict(ranks=ranks,quadratic_ranks=quad,pass_all=len(F)==len(C)),layers

def main():
 data=pickle.load(open(Path(__file__).parent/'ccz_states.pkl','rb'));one=data['one']
 family=Path(__import__('os').environ.get('GVQCC_CHEM_FAMILY',str(Path(__file__).resolve().parents[1]/'v110/chemistry')));c=V.parse(family/'angle_k_0.kmb')
 records=[];saved={}
 for idx,op,rows in data['states']:
  if idx<25699 or (op.raw&127)!=80:continue
  rr=rows[:]
  if idx==25699:rr[op.wires[2]]^=rr[op.wires[0]]&rr[op.wires[1]];idx+=1
  final=rr[:];V.run(dict(ops=c['ops'][idx:]),final,one)
  F=basis([one]+final);C=basis(F+rr)
  res,layers=closure(C,F,one);res.update(index=idx,rank=len(C),protected_rank=len(F));records.append(res)
  print(res,flush=True)
  saved[idx]=dict(C=C,F=F,rows=rr,final=final,layers=layers,one=one)
  if res['pass_all']:
   print('FOUND FREE-ERASABLE TAIL',idx,flush=True);break
 (Path(__file__).parent/'tail_closure_result.json').write_text(json.dumps(records,indent=2)+'\n')
 pickle.dump(saved,open(Path(__file__).parent/'tail_closure_states.pkl','wb'))

if __name__=='__main__':main()