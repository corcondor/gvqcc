"""Core packed-Boolean V41 algorithms; Python 3.11+, stdlib.
The conversation archive provides the actual PR94 graph loader, compiler and
full receipts. Integer bit j denotes row j of a finite reachable domain.
Do NOT treat an observation-space decoder as a complete physical circuit.
"""
from itertools import combinations

def bits(x):
    while x:
        y=x & -x
        yield y.bit_length()-1
        x ^= y

def xor_sum(values, mask):
    out=0
    for i in bits(mask):
        out ^= values[i]
    return out

def nullspace(cols):
    """Kernel of the linear map whose columns are packed bit vectors."""
    B={}; ker=[]
    for j,col in enumerate(cols):
        m=1<<j
        while col:
            p=col.bit_length()-1
            if p not in B:
                B[p]=(col,m)
                break
            q,t=B[p]; col^=q; m^=t
        if not col:
            ker.append(m)
    return len(B),ker

def quadratic_terms(n):
    return [()]+[(i,) for i in range(n)]+list(combinations(range(n),2))

def monomial(values, term, one):
    z=one
    for i in term: z &= values[i]
    return z

def restrict_exact_kernel(values, sample_kernel, nrows):
    """Every exact relation lies in the sample kernel. Restrict that entire
    subspace (not just one proposed solution) on all remaining rows."""
    terms=quadratic_terms(len(values)); ker=list(sample_kernel); cursor=0
    while cursor<nrows and ker:
        size=min(nrows-cursor,65536 if cursor<196608 else nrows-cursor)
        mask=(1<<size)-1
        sliced=[(v>>cursor)&mask for v in values]
        cols=[monomial(sliced,t,mask) for t in terms]
        residuals=[xor_sum(cols,k) for k in ker]
        _, nk=nullspace(residuals)
        ker=[xor_sum(ker,k) for k in nk]
        cursor+=size
    return ker

def cofactor_cramer(a,b,c,d,r,s,repair_x,repair_y,one):
    """All operands are functions of the RETAINED coordinates.
    If a*x+b*y=r and c*x+d*y=s on the legal domain,
    Cramer numerators equal det*x and det*y. The two repair functions
    must be valid on det=0. No postselection."""
    det=(a&d)^(b&c)
    exceptional=one^det
    return ((d&r)^(b&s)^(exceptional&repair_x),
            (a&s)^(c&r)^(exceptional&repair_y))

def cofactor_glue(derivatives, constants, repair, one):
    """For a direction v and omitted coordinate p, exact P_i=0 implies
    P_i(projected_state)=p*D_v P_i. Select the first available relation;
    repair the exceptional set where all directional derivatives vanish."""
    covered=out=0
    for delta, rhs in zip(derivatives,constants):
        out ^= rhs & (one^covered)
        covered |= delta
    return out ^ ((one^covered)&repair)

def project_direction(values, direction):
    p=(direction & -direction).bit_length()-1
    return p,[v ^ (values[p] if direction>>i&1 else 0)
              for i,v in enumerate(values) if i!=p]
