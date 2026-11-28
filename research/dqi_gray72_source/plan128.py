"""Exact 56-anchor extension of #340; no verifier-dependent anchor selection."""
import sys
from pathlib import Path
import numpy as np
import source72 as s
p=Path(sys.argv[1]);out=Path(sys.argv[2])
c=np.fromstring(p.read_text().splitlines()[-1],sep=' ',dtype=np.int32)
a=[round(s.N*j/128) for j in range(128)]; extras=[x for x in a if x not in s.A72]
assert len(extras)==56
with out.open('w') as f:
 print(len(extras),file=f)
 for j,an in enumerate(extras):
  print(an,*s.mat(c[an]),file=f)
  ids=np.delete(np.arange(s.N+1),an)
  ids=ids[((np.arange(512)*s.N+((j*137)%s.N))//512)%s.N]
  assert len(set(ids))==512
  z=c[ids]^c[an];assert np.all(z)
  np.savetxt(f,np.column_stack([ids,s.mat(s.inv(z))]),fmt='%d')
 print(*c,file=f)
print('additional anchors',len(extras),'all',len(extras)+len(s.A72))
