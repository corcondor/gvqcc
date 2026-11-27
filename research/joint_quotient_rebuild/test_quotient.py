"""Independent small-space exhaustive right-factor verification."""
from random import Random
from quotient_product import basis,lin,directions
import json
r=Random(20261128); tests=0;products=0
for _ in range(256):
 n=r.randrange(3,11);one=(1<<n)-1
 C=basis([one]+[r.randrange(1<<n)for i in range(r.randrange(1,6))]);E=basis(C+[r.randrange(1<<n)for i in range(r.randrange(1,4))])[len(C):]
 allC=[lin(C,j)for j in range(1<<len(C))];lookup={lin(C+E,j):j>>len(C) for j in range(1<<len(C+E))}
 for u in allC:
  exact={lookup[u&v] for v in allC if u&v in lookup}-{0}
  got=directions(C,E,u,one);assert set(got)==exact
  for k,(a,b,w) in got.items():assert a==u and b in allC and w==a&b and lookup[w]==k
  tests+=1;products+=len(exact)
receipt={'spaces':256,'exhaustive_left_factor_tests':tests,'nonzero_class_witnesses':products,'errors':0}
print(receipt);open('test_quotient.json','w').write(json.dumps(receipt,indent=2)+'\n')
