from collections import Counter,defaultdict
from itertools import combinations
import json

GATES=((3,48),(13,208),(14,224),(28,205),(31,225),(52,71),
       (40,138),(46,194),(77,148),(91,190),(127,135),(120,143),(121,158))
OUTPUTS=((8,2383),(27,4535),(20,7604),(7,6094),
         (1,5274),(154,554),(69,2108),(247,4115))

def xor_rows(rows):
 out=0
 for r in rows:out^=r
 return out

def wedge(a,b,n=8):
 return sum((((a>>i)*(b>>j))^((a>>j)*(b>>i)))%2<<k
            for k,(i,j) in enumerate(combinations(range(n),2)))

def basis(rows):
 p={}
 for x in rows:
  y=reduce(x,p)
  if y:p[y.bit_length()-1]=y
 return p

def reduce(x,p):
 for i,row in sorted(p.items(),reverse=True):
  if x>>i&1:x^=row
 return x

def span(rows):
 V=[0]
 for row in rows:V += [v^row for v in V]
 return V

if __name__=='__main__':
 terms=[wedge(a,b) for a,b in GATES]
 A=[xor_rows(v for i,v in enumerate(terms) if mask>>i&1) for _,mask in OUTPUTS]
 projection=basis(A)
 atoms={}
 for a,b in combinations(range(1,256),2):
  w=wedge(a,b)
  atoms.setdefault(w,(a,b))
 assert len(atoms)==10795
 buckets=defaultdict(list)
 for w in sorted(atoms):
  buckets[reduce(w,projection)].append(w)
 U=list(basis(reduce(t,projection) for t in terms).values())
 V=span(U)
 print('ranks:',len(projection),len(basis(terms)),len(U),'quotient distribution',Counter(len(row) for row in buckets.values()),'base atoms inside',sum(len(buckets.get(v,[])) for v in V))
 print('decomposable target span:',buckets.get(0),'base quotient weights:', [(v,len(buckets.get(v,[]))) for v in V if v in buckets])
 cases=[]
 for normal in range(1,1<<len(U)):
  W=[v for j,v in enumerate(V) if ((j&normal).bit_count()&1)==0]
  a=[w for v in W for w in buckets.get(v,[])]
  r=len(basis(a))
  cases.append((W,r))
 print('current hyperplane counts',Counter(r for _,r in cases))
 bkeys=sorted(buckets)
 compact=dict(input_basis=A, gate_products=terms, initial_quotient_basis=U,
              atoms=[[w,reduce(w,projection),a,b] for w,(a,b) in atoms.items()])
 open('joint_quad_data.json','w').write(json.dumps(compact)+'\n')
 with open('joint_quad_data.txt','w') as f:
  f.write(f'{len(A)} {len(U)} {len(atoms)}\n')
  f.write(' '.join(map(str,A))+'\n')
  f.write(' '.join(map(str,U))+'\n')
  for row in compact['atoms']:f.write(' '.join(map(str,row))+'\n')
