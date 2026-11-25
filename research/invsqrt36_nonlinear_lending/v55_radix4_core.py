"""Portable independent exact integer V55 retained-term model checker.
Run python3 v55_radix4_core.py with numpy. No native gate or score claim.
"""
import math, hashlib
import numpy as np
C=np.array([[4294967250,-268433096,25146592,-2565904,219200],[4049333976,-224961728,18736560,-1706016,132768],[3841535520,-192076044,14399824,-1183440,84576],[3662760408,-166488668,11347944,-849696,56128],[3506826108,-146117476,9130104,-627744,38560],[3369249544,-129586340,7474672,-475040,27264],[3246690100,-115953096,6210792,-366928,19776],[3136600628,-104553268,5226984,-288480,14624],[3037000500,-94906204,4448248,-230320,11040],[2946323258,-86656524,3822736,-186416,8480],[2863311530,-79536400,3313760,-152688,6592],[2786942794,-73340576,2894832,-126432,5216],[2716375826,-67909376,2546456,-105696,4160],[2650911368,-63116924,2254064,-89136,3360],[2589962728,-58862776,2006600,-75760,2720],[2533033520,-55065936,1795560,-64864,2240],[2479700524,-51660420,1614336,-55904,1856],[2429600400,-48592004,1457720,-48464,1568],[2382419202,-45815748,1321576,-42256,1312],[2337884076,-43294144,1202584,-37040,1120],[2295756588,-40995648,1098072,-32608,928],[2255827340,-38893572,1005848,-28848,800],[2217911576,-36965192,924112,-25616,704],[2181845568,-35191056,851384,-22848,608]],dtype=np.int64)
def check():
 N=3133452
 x=np.arange(1,N+1,dtype=np.int64); e=np.zeros_like(x)
 for j in range(1,11):e[x>=1<<(2*j)]=j
 U=x<<(2*(10-e));assert U.min()==1<<20 and U.max()<1<<22
 a=(U>>17)-8;t=U&((1<<17)-1);v=C[a,4].copy();pc=0
 for j in reversed(range(4)):
  av=np.abs(v);p=np.zeros_like(v);w=int(av.max()).bit_length()
  for i in range(w):
   for k in range(max(0,17-i),17):
    p+=(((av>>i)&1)*((t>>k)&1))<<(i+k-17);pc+=1
  v=C[a,j]+np.sign(v)*p
 sh=32+e-34;q=np.empty_like(v)
 for k in np.unique(sh):
  m=sh==k;q[m]=(v[m]+(1<<(int(k)-1)))>>int(k) if k>0 else v[m]<<int(-k)
 ref=np.empty(N,np.uint64);tol=np.empty(N,np.int64)
 for xx in range(1,N+1):
  r=math.isqrt((1<<130)//xx);ref[xx-1]=((r+1)//2)%(1<<64);tol[xx-1]=r>>25
 err=np.abs(((q.astype(np.uint64)<<np.uint64(30))-ref).view(np.int64))
 assert np.all(err<=tol) and pc==969 and int((tol-err).min())==54096592
 sha=hashlib.sha256(q.astype('<i8').tobytes()).hexdigest()
 assert sha=='51e4370ddd9b1029b69163aca604697c2b0130da63e9c49b774c6a61d47d9477'
 print('PASS',N,pc,sha,float(np.max(err/tol)))
if __name__=='__main__':check()
