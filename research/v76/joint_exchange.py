"""V76: nonlinear state/phase transport in a reachable Boolean function algebra.
An exact joint exchange changes the physical coordinate w to v.  Never use
a sampled equality as a certificate. Tables are Python ints, with one bit
per legal input; the caller supplies the complete care domain.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Quadratic:
    linear: tuple[int, ...] = ()
    products: tuple[tuple[int, int], ...] = ()
    constant: int = 0
    def evaluate(self, xs, mask):
        out = mask if self.constant else 0
        for j in self.linear:
            out ^= xs[j]
        for j,k in self.products:
            out ^= xs[j] & xs[k]
        return out & mask

def fit_quadratic(xs, target, mask):
    """Solve in the entire current carrier space, not a fixed product list."""
    terms = [(-1,-1)] + [(j,-1) for j in range(len(xs))]
    terms += [(j,k) for j in range(len(xs)) for k in range(j+1,len(xs))]
    basis = {}
    def reduce(z,c):
        while z:
            j = z.bit_length()-1
            if j not in basis:
                break
            a,b = basis[j]
            z ^= a
            c ^= b
        return z,c
    for j,(a,b) in enumerate(terms):
        z = mask if a<0 else xs[a] if b<0 else xs[a]&xs[b]
        z,c = reduce(z&mask,1<<j)
        if z:
            basis[z.bit_length()-1] = z,c
    rem,c = reduce(target&mask,0)
    if rem:
        return None
    linear = []
    products = []
    constant = 0
    for j,(a,b) in enumerate(terms):
        if c>>j&1:
            if a<0:
                constant ^= 1
            elif b<0:
                linear.append(a)
            else:
                products.append((a,b))
    ans = Quadratic(tuple(linear),tuple(products),constant)
    assert ans.evaluate(xs,mask)==(target&mask)
    return ans

def joint_exchange(w,v,z,g,mask):
    """g is the exact pulled-back correction, in the chart (v,z).
    If w=g and v+w=h(z), emit h on the w slot, re-label it v, and
    virtualize the measurement of w with its old independent outcome bit.
    Returning None prohibits the rewrite.
    """
    if ((w^g.evaluate([v,*z],mask))&mask):
        return None
    return fit_quadratic(z,w^v,mask)

def dual_delta(f0,f1,g0,g1,mask):
    """For v=f0+w*f1 and w=g0+v*g1 in GF(2), eliminate w and v."""
    return (f0 ^ ((mask^f1)&(g0^(f0&g1))))&mask

def self_test():
    count=0
    for f0 in range(2):
        for f1 in range(2):
            for g0 in range(2):
                for g1 in range(2):
                    for w in range(2):
                        for v in range(2):
                            if v==(f0^(w&f1)) and w==(g0^(v&g1)):
                                assert (w^v)==dual_delta(f0,f1,g0,g1,1)
                                count+=1
    mask=15
    x,y=10,12
    w=x&y
    v=w^x
    correction=Quadratic(products=((1,2),))
    q=joint_exchange(w,v,[x,y],correction,mask)
    assert q is not None and q.evaluate([x,y],mask)==x
    assert joint_exchange(w,v,[x,y],Quadratic(),mask) is None
    print("joint-law legal assignments:",count)
if __name__=="__main__":
    self_test()
