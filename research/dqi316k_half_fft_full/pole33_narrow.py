import os,sys
from pathlib import Path
import kickmix as km
sys.modules["circ"]=km
ROOT=Path(os.environ['DQI_KIT'])
sys.path[:0]=[str(ROOT/'exp/new/a16'),str(ROOT/'exp/new/a10'),str(ROOT/'exp/new/a07')]
import lowclean as lc
import lowclean_norm5log7 as ln
from transport42_lean import gate_tape
F=km.GF2Field(12);K=3104;K2=F.mul(K,K)
def word(b):return b.alloc_qubits(12)
def flat(*xs):return km.array([q for x in xs for q in x])
def ix(b,x,y,z):gate_tape(b,x,y,z)
def add(b,x,z,h=True):b.gf2_iadd(x,target=z,field=F,control=h)
def lmap(b,x,cols):lc.ar.linear_inplace(b,x,cols)
def square(b,x,rev=False):lmap(b,x,tuple(F.pow(1<<i,2048 if rev else 2) for i in range(12)))
def const(b,x,c):lmap(b,x,tuple(F.mul(c,1<<i) for i in range(12)))
def constadd(b,c,x,z,h=True):
 if h is True or not c:
  if c:
   for i in range(12):
    a=F.mul(c,1<<i)
    for j in range(12):
     if a>>j&1:b.cx(x[i],z[j])
  return
 const(b,x,c)
 for i in range(12):b.ccx(h,x[i],z[i])
 const(b,x,F.invert(c))
def qmul(b,x,y):
 z=word(b);ix(b,x,y,z);return z
def unmul(b,x,y,z):lc.ar.erase_product(b,x,y,z);b.free(z)
def scale(b,x,f,h,rev=False):
 t=word(b);b.x(t[0]);add(b,f,t,h);b.cx(h,t[0])
 ln.scale(b,x,t,rev)
 m=b.alloc_bits(12);b.hmr(t,m)
 b.z(m[0]);b.cz(h,m[0])
 for j in range(12):b.ccz(h,f[j],m[j])
 b.free(m);b.free(t)
def inverse_inplace(b,x,h):
 t=word(b);add(b,x,t);lc.inverse(b,t);b.cswap(h,x,t);lc.inverse(b,t);add(b,x,t);b.free(t)
def product_add(b,x,y,z,h):
 t=qmul(b,x,y);add(b,t,z,h);unmul(b,x,y,t)
def computeG(b,a,c,d,p,q,G):
 square(b,d);ix(b,q,d,G);square(b,d,True)
 square(b,p);ix(b,p,a,G);square(b,p,True)
 pc=qmul(b,p,c);ix(b,pc,d,G);unmul(b,p,c,pc)
def guards(b,head,a,c,d,p,q,flag,pole=None):
 G=word(b);computeG(b,a,c,d,p,q,G)
 z=[]
 for w,nonzero,borrow in [(flat(*head),False,flat(a,c)),(a,True,c),(d,True,a),(q,True,a),(G,True,a)]:
  v=b.alloc_qubits(1)[0];lc.zero_toggle(b,w,v,borrow)
  if nonzero:b.x(v)
  z.append((v,w,nonzero,borrow))
 if pole is not None:b.x(pole)
 cs=[v for v,_,_,_ in z]+([] if pole is None else [pole]);lc.mcx_dirty(b,cs,flag,a)
 if pole is not None:b.x(pole)
 for v,w,nonzero,borrow in reversed(z):
  if nonzero:b.x(v)
  lc.zero_toggle(b,w,v,borrow);b.free(v)
 computeG(b,a,c,d,p,q,G);b.free(G)
def chart(b,N,D,p,q,h,reverse=False):
 n0,n1,d=N;a,v=D
 def reduce_N():
  add(b,p,d,h);constadd(b,K,d,n0,h);add(b,d,n1,h);constadd(b,K,p,n1,h)
 def expand_N():
  constadd(b,K,p,n1,h);add(b,d,n1,h);constadd(b,K,d,n0,h);add(b,p,d,h)
 def shift_b():product_add(b,p,a,v,h)
 def first_ratios(rev):
  if rev:scale(b,v,d,h,False);shift_b();scale(b,a,d,h,False)
  else:scale(b,a,d,h,True);shift_b();scale(b,v,d,h,True)
 def second_coeff(rev):
  def multiply_f(rev):
   f=qmul(b,p,v);ln.scale(b,f,q,True);b.x(f[0]);scale(b,d,f,h,rev);b.x(f[0]);ln.scale(b,f,q);unmul(b,p,v,f)
  def shear():
   lc.inverse(b,q);square(b,p);z=qmul(b,p,q)
   product_add(b,z,a,d,h)
   unmul(b,p,q,z);square(b,p,True);lc.inverse(b,q)
  if rev:shear();multiply_f(True)
  else:multiply_f(False);shear()
 def low_coeff(rev):
  const(b,q,K2)
  def deriv(rev):
   square(b,a);lc.inverse(b,q);f=qmul(b,a,q)
   scale(b,v,f,h,rev)
   unmul(b,a,q,f);lc.inverse(b,q);square(b,a,True)
  if rev:deriv(True);scale(b,a,q,h,True);inverse_inplace(b,a,h)
  else:inverse_inplace(b,a,h);scale(b,a,q,h);deriv(False)
  const(b,q,F.invert(K2))
 def route(rev):
  if rev:constadd(b,K,q,a,h);add(b,q,v,h);b.cswap(h,n1,v);b.cswap(h,n0,a)
  else:b.cswap(h,n0,a);b.cswap(h,n1,v);constadd(b,K,q,a,h);add(b,q,v,h)
 if reverse:route(True);low_coeff(True);second_coeff(True);first_ratios(True);expand_N()
 else:reduce_N();first_ratios(False);second_coeff(False);low_coeff(False);route(False)

