#!/usr/bin/env python3
"""Four inverse output functions remain independent modulo quadratic terms on C!=0."""
import kickmix as km

def span_rank(words):
    basis={}
    for v in words:
        while v:
            j=v.bit_length()-1
            if j not in basis:
                basis[j]=v
                break
            v^=basis[j]
    return len(basis)

f=km.GF2Field(4)
one=(1<<15)-1
xs=[sum(((a>>i)&1)<<(a-1) for a in range(1,16)) for i in range(4)]
inverse_coords=[sum(((f.invert(a)>>i)&1)<<(a-1) for a in range(1,16))
                for i in range(4)]
degree_two=[one,*xs,*(xs[i]&xs[j] for i in range(4) for j in range(i))]
old=span_rank(degree_two)
new=span_rank(degree_two+inverse_coords)
assert (old,new)==(11,15)
print('quadratic span=11, quadratic+inverse span=15 on 15 nonzero values')
