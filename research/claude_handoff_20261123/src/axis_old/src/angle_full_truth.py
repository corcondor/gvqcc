import numpy as np

def anf_full7(delta,lowbits=4):
 """Full 7-bit word ANF (including sign bit), no signed-gauge assumptions.
 Output shape L,H,7J. Padded addresses in last high block are zero.
 """
 delta=np.asarray(delta,dtype=np.int64)
 count,J=delta.shape;L=1<<lowbits;H=(count+L-1)//L;hb=max(1,(H-1).bit_length())
 data=np.zeros((1<<hb,L,7*J),dtype=np.uint8)
 flat=data.reshape(-1,7*J)
 for j in range(J):
  for b in range(7):flat[:count,j*7+b]=((delta[:,j]>>b)&1).astype(np.uint8)
 def mobius(A,axis):
  A=np.moveaxis(A,axis,0).copy();sz=A.shape[0];v=1
  while v<sz:
   i=np.arange(sz,dtype=np.int32);i=i[(i&v)>0];A[i]^=A[i^v];v <<= 1
  return np.moveaxis(A,0,axis)
 return mobius(mobius(data,0),1)[:H].transpose(1,0,2).copy()