from tensor_audit import *
from classify import extract,basis,coord
import sys
for meta,g in parse(sys.argv[1]):
 dirs=[w for a,b,w in extract(g)]
 assert rank(dirs)==24
 rows=[sum((w>>q&1)<<i for i,w in enumerate(dirs)) for q in range(Q)]
 # Give each wire's dependence on the 24 independent output coordinates.
 f=coord(basis(rows))
 print(*meta,*(f(x) for x in rows))
