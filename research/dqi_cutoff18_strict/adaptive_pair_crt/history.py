"""Exact rank/unrank of one-slot and two-slot adaptive-pivot macros."""
import random

F=[0,1]
for _ in range(40):
    F.append(F[-1]+F[-2])

def append(H,l,jump):
    assert 0<=l<=35 and F[l+2]-1<=H<F[l+3]-1
    d=2 if jump else 1
    assert l+d<=35
    return H+(F[l+4] if jump else F[l+1]),l+d

def pop(H,l):
    assert 0<l<=35 and F[l+2]-1<=H<F[l+3]-1
    jump=l>=2 and H>=F[l+2]-1+F[l]
    return H-(F[l+2] if jump else F[l]),l-(2 if jump else 1),jump

def decode(H):
    assert 0<=H<F[38]-1
    l=next(i for i in range(36) if F[i+2]-1<=H<F[i+3]-1)
    out=[]
    while l:
        H,l,j=pop(H,l)
        out.append(j)
    assert H==0
    return list(reversed(out))

def test():
    count=0
    for l in range(21):
        for H in range(F[l+2]-1,F[l+3]-1):
            a,b=0,0
            for j in decode(H):
                a,b=append(a,b,j)
            assert (a,b)==(H,l)
            count+=1
    rng=random.Random(229233)
    for _ in range(4096):
        H=rng.randrange(F[38]-1)
        a,b=0,0
        for j in decode(H):
            a,b=append(a,b,j)
        assert a==H
    assert F[38]-1==39088168 and F[38]-1<2**26
    print(dict(exhaustive=count,sampled=4096,history_bits=26))

if __name__=='__main__':
    test()
