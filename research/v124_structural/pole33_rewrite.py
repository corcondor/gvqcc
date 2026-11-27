"""Apply the V124 chart changes to the V123 pole33_narrow.py source.
Use only with the pinned public-kit implementation. The HMR phase repayment
assumes clean product temporaries, and the two retained inputs are disjoint
from the payload being changed.
"""
from pathlib import Path
import sys

REPLACEMENTS = [
    ("def unmul(b,x,y,z):ix(b,x,y,z);b.free(z)",
     "def unmul(b,x,y,z):lc.ar.erase_product(b,x,y,z);b.free(z)"),
    (" b.cx(h,t[0]);add(b,f,t,h);b.x(t[0]);b.free(t)",
     """ # t = 1 + h*(f+1). HMR and exact linear/degree-two phase repayment.
 m=b.alloc_bits(12);b.hmr(t,m)
 b.z(m[0])
 b.cz(h,m[0])
 for j in range(12):b.ccz(h,f[j],m[j])
 b.free(m);b.free(t)"""),
    ("""   lc.inverse(b,q);square(b,p);z=qmul(b,p,q);square(b,p,True);lc.inverse(b,q)
   product_add(b,z,a,d,h)
   lc.inverse(b,q);square(b,p);unmul(b,p,q,z);square(b,p,True);lc.inverse(b,q)""",
     """   lc.inverse(b,q);square(b,p);z=qmul(b,p,q)
   product_add(b,z,a,d,h)
   unmul(b,p,q,z);square(b,p,True);lc.inverse(b,q)"""),
    ("""   square(b,a);lc.inverse(b,q);f=qmul(b,a,q);lc.inverse(b,q);square(b,a,True)
   scale(b,v,f,h,rev)
   square(b,a);lc.inverse(b,q);unmul(b,a,q,f);lc.inverse(b,q);square(b,a,True)""",
     """   square(b,a);lc.inverse(b,q);f=qmul(b,a,q)
   scale(b,v,f,h,rev)
   unmul(b,a,q,f);lc.inverse(b,q);square(b,a,True)"""),
]

def rewrite(source):
    for old,new in REPLACEMENTS:
        if source.count(old) != 1:
            raise ValueError("Unexpected source; refusing to rewrite: " + old)
        source=source.replace(old,new,1)
    return source

if __name__ == "__main__":
    src,dst=map(Path,sys.argv[1:])
    dst.write_text(rewrite(src.read_text()))
