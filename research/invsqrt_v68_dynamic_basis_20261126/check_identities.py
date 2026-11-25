from itertools import product
for f,a,b in product(range(2),repeat=3):
    assert (f&a)^(f&(a^b))==f&b
    assert (f&a)^(f&b)==f&(a^b)
for a,b,c,u,v,w in product(range(2),repeat=6):
    assert (a&u)^(b&v)^(c&w)==((a^b^c)&w)^(a&(u^v))^((a^b)&(v^w))
for x,y,a in product(range(2),repeat=3):
    X,Y,g=x^a,y,x^y
    Y^=X;Y^=g;X^=Y;Y^=g;Y^=X
    assert (X,Y)==(x,y^a)
print('88 Boolean cases PASS (Python; not Lean)')
