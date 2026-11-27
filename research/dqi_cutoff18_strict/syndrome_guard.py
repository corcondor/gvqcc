"""Research-only, fail-closed GF(4096) 0/1/2 sparse-syndrome witness.

Not a KMB repair. Do NOT mistake a witness for a corrupted output for a
certificate that the original syndrome was restored. Check the original
input, mask, ancillas and every measurement branch separately.
"""
from dataclasses import dataclass
MOD = 0x1053

def mul(a,b):
    assert 0 <= a < 4096 and 0 <= b < 4096
    z=0
    while b:
        if b & 1: z ^= a
        b >>= 1
        a <<= 1
        if a & 4096: a ^= MOD
    return z

def power(a,n):
    assert n>=0
    z=1
    while n:
        if n & 1: z=mul(z,a)
        a=mul(a,a);n>>=1
    return z

def inv(a):
    if not a: raise ZeroDivisionError
    return power(a,4094)

@dataclass(frozen=True)
class Certificate:
    roots: tuple
    magnitudes: tuple
    def moments(self):
        out=[0]*70
        for x,a in zip(self.roots,self.magnitudes):
            v=mul(x,a)
            for k in range(70):
                out[k]^=v
                v=mul(v,x)
        return out

def certify_rank_le_two(Y):
    if len(Y)!=70 or any(not 0<=v<4096 for v in Y):
        raise ValueError("70 12-bit elements required")
    if not any(Y): return Certificate((),())
    s0,s1,s2,s3=Y[:4]
    if s0:
        x=mul(s1,inv(s0))
        if x:
            a=mul(s0,inv(x))
            c=Certificate((x,),(a,))
            if a and c.moments()==Y: return c
    D=mul(s0,s2)^mul(s1,s1)
    if not D: return None # D=0 does NOT prove rank<=1!
    u=mul(mul(s0,s3)^mul(s1,s2),inv(D))
    v=mul(mul(s1,s3)^mul(s2,s2),inv(D))
    roots=[x for x in range(1,4096) if mul(x,x)^mul(u,x)^v==0]
    if len(roots)!=2: return None
    x,z=roots
    A=mul(s1^mul(z,s0),inv(x^z))
    B=s0^A
    if not A or not B: return None
    c=Certificate((x,z),(mul(A,inv(x)),mul(B,inv(z))))
    return c if c.moments()==Y else None

def mask_phase(c,mask):
    if len(mask)!=4095: raise ValueError("4095 magnitude masks required")
    logs={power(2,k):k for k in range(4095)}
    assert len(logs)==4095
    return sum((mask[logs[x]]&a).bit_count()&1
               for x,a in zip(c.roots,c.magnitudes))&1
