"""Reuse exact #237 rank-42 linear skeleton in the HMR adjoint.
Whole #247 invariant pad guard is emitted with identical public transform.
No syndrome measurements, no input-dependent host branch.
"""
import sys
from pathlib import Path
import crt882 as C
import joint_phase as J
import invariant247 as Base
import kickmix as km
def product_clear42(b,a,c,z):
    assert len(a)==len(c)==len(z)==12
    assert len(set(a+c+z))==36
    mask=J.measure(b,z)
    # Reverse input frames and transpose output frames, not inverse mask bit copy.
    q=a+c+mask
    for op,*args in reversed(C.GATES):
        if op==1:
            x,y=args
            assert x//12==y//12
            if x<24:b.cx(q[x],q[y])
            else:b.cx(q[y],q[x])
        else:
            x,y,t=args
            assert x<12<=y<24<=t
            b.ccz(q[x],q[y],q[t])
    J.cclear(b,mask)
def scale42(self,x,f,fi,tmp):
    self.mul(x,f,tmp)
    for a,b in zip(x,tmp):self.b.swap(a,b)
    product_clear42(self.b,x,fi,tmp)
Base.Guard.scale=scale42
if __name__=='__main__':Base.main()
