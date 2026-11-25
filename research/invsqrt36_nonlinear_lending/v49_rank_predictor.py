"""Low-rank normalized mantissa tensor; fixed-point integer Horner audit.
A finite rank factorization, NOT the asymptotic 9/4 matrix multiplication algorithm.
Output is a whole-oracle numeric spec; reversible Horner is not emitted here.
"""
import math,json,time
from pathlib import Path
N=3133452;Q=1<<48;M=1<<35;E=M>>24;LO=(M-E)**2;HI=(M+E)**2
def coeff(h,d):
 rows=[]
 for i in range(1<<h):
  a=1+(i+.5)/2**h
  rows.append([round(Q*(-1)**j*math.comb(2*j,j)/4**j/a**(j+.5)/2**(h*j))for j in range(d+1)])
 return rows
def rounddiv(n,d):
 return (n+d//2)//d if n>=0 else -((-n+d//2)//d)
def test(h,d):
 T=coeff(h,d);q2=round(Q/math.sqrt(2));worst=0.;at=0;t=time.time();bad=0
 for x in range(1,N+1):
  e=x.bit_length()-1;mant=(x-(1<<e))<<(21-e);idx=mant>>(21-h);den=1<<(21-h);z=2*(mant&(den-1))-den
  c=T[idx];v=c[-1]
  for a in reversed(c[:-1]):v=a+rounddiv(v*z,2*den)
  if e&1:v=rounddiv(v*q2,Q)
  y=rounddiv(v*M,Q<<(e//2));err=abs(y/M*math.sqrt(x)-1)*2**24
  if err>worst:worst=err;at=x
  bad+=not LO<=x*y*y<=HI
 rho=1/((1<<(h+1))+1);tail=(rho**(d+1)/(1-rho))*math.sqrt(1+rho)
 rec=dict(h=h,degree=d,rank=d+1,coefficients=(1<<h)*(d+1),fixed_coefficient_bits=48,phase_bits=35,actual_legal=N,bad=int(bad),worst_relative_over_tolerance=worst,worst_x=at,analytic_relative_bound=tail,seconds=time.time()-t,table=T,odd_scale=q2,physical_emitted=False)
 print({k:v for k,v in rec.items()if k!='table'},flush=True);return rec
if __name__=='__main__':
 rows=[]
 for h,d in [(4,4),(3,5),(2,7),(1,10)]:
  rows.append(test(h,d));Path('v49_rank_predictor.json').write_text(json.dumps(rows,indent=2))
