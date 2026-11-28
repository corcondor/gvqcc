# small GF(2) helpers on python int bit vectors
class Ech:
    __slots__=('piv','n')
    def __init__(self, rows=()):
        self.piv={}; self.n=0
        for r in rows: self.add(r)
    def add(self, v):
        piv=self.piv
        while v:
            h=v.bit_length()-1; p=piv.get(h)
            if p is None: piv[h]=v; self.n+=1; return True
            v^=p
        return False
    def reduce(self, v):
        piv=self.piv
        while v:
            h=v.bit_length()-1; p=piv.get(h)
            if p is None: return v
            v^=p
        return 0
    def copy(self):
        e=Ech(); e.piv=dict(self.piv); e.n=self.n; return e

class CombEch:
    """echelon basis with combination tracking: add(v, tag) ; solve(v) -> combo or None"""
    def __init__(self):
        self.piv={}
    def add(self, v, c):
        while v:
            h=v.bit_length()-1; p=self.piv.get(h)
            if p is None: self.piv[h]=(v,c); return None
            v^=p[0]; c^=p[1]
        return c   # dependency
    def solve(self, v):
        c=0
        while v:
            h=v.bit_length()-1; p=self.piv.get(h)
            if p is None: return None
            v^=p[0]; c^=p[1]
        return c

def solve_linear(rows, rhs, nvars):
    """solve rows[i].x = rhs[i] (rows: int bitmask over nvars). returns (particular, nullspace basis) or None."""
    piv={}   # pivot bit -> (row, rhsbit)
    for r,b in zip(rows,rhs):
        while r:
            h=r.bit_length()-1; p=piv.get(h)
            if p is None: piv[h]=(r,b); break
            r^=p[0]; b^=p[1]
        else:
            if b: return None
    keys=sorted(piv)
    for h in keys:
        r,b=piv[h]
        for h2 in keys:
            if h2!=h and (piv[h2][0]>>h)&1:
                piv[h2]=(piv[h2][0]^r, piv[h2][1]^b)
    x=0
    for h,(r,b) in piv.items():
        if b: x|=1<<h
    free=[c for c in range(nvars) if c not in piv]
    null=[]
    for f in free:
        v=1<<f
        for h,(r,b) in piv.items():
            if (r>>f)&1: v|=1<<h
        null.append(v)
    return x,null
