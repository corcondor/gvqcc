"""Finite exact Boolean identities underlying V71; independent of KMB."""
from itertools import product
n=0
for f,g,k,d,h in product(range(2),repeat=5):
    assert ((f&g&d)^(f&k&h)) == ((f&(g^k)&d)^(f&k&(h^d)))
    assert ((f&g&d)^(k&h&d)) == ((f&(g^h)&d)^((k^f)&h&d))
    assert (f&g&d) == ((f&(g^k)&d)^(f&k&d))
    n+=3
for u,v,w,z in product(range(2),repeat=4):
    assert ((u&v)^(w&z)) == ((u&(v^z))^((u^w)&z))
    if (u^v)==(w^z): assert u^w^z==v
    n+=1
for m,g in product(range(2),repeat=2):
    assert ((m&g)^(m&g))==0
    assert g^(g^m)==m
    n+=2
print("Boolean identities PASS",n)
