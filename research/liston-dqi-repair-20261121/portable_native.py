"""Portable native KMB primitives extracted without semantic edits.

Only Python standard-library modules and NumPy are required. 
"""
from pathlib import Path
import hashlib, mmap, struct
import numpy as np


class Native:
    def __init__(self,path):
        self.file=Path(path).open('rb');self.raw=mmap.mmap(self.file.fileno(),0,access=mmap.ACCESS_READ)
        self.header=list(struct.unpack_from('<4I9Q',self.raw,16));self.sections={};self.regs=[];self.a={}
        p=104
        while p<len(self.raw):
            k,n=struct.unpack_from('<QQ',self.raw,p)
            if k==0:self.regs.append((p,n+16))
            else:
                self.sections[k]=(p+16,n)
                if k<=9:self.a[k]=np.frombuffer(self.raw,dtype=np.uint8 if k==1 else '<u4',count=n//(1 if k==1 else 4),offset=p+16)
            p+=n+16
        assert set(self.a)==set(range(1,10))


def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def ahash(a):return hashlib.sha256(memoryview(a)).hexdigest()


def registers(c):return hashlib.sha256(b''.join(memoryview(c.raw)[p:p+n] for p,n in c.regs)).hexdigest()


def positions(c,cuts):
 out={};cursor=np.zeros(9,dtype=np.int64);last=0;depth=0
 for cut in sorted(set(cuts)):
  assert last<=cut<=c.header[4];counts=np.zeros(256,dtype=np.int64)
  for at in range(last,cut,1<<20):counts+=np.bincount(c.a[1][at:min(cut,at+(1<<20))],minlength=256)
  cats=np.arange(256)&48
  n3=int(counts[cats==48].sum());n2=int(counts[cats==32].sum());n1=int(counts[cats==16].sum())
  cursor+=np.array([cut-last,n3,n3,n3,n2,n2,n1,int(counts[64:128].sum()+counts[192:].sum()),int(counts[128:].sum())])
  depth+=int(counts[129]-counts[1]);out[cut]=(cursor.copy(),depth);last=cut
 return out


def piece(c,pos,start,end,k):return c.a[k][int(pos[start][0][k-1]):int(pos[end][0][k-1])]


def same(c,p,s,e,d,q,t,u):
 assert e-s==u-t
 hashes=[]
 for k in range(1,10):
  a,b=piece(c,p,s,e,k),piece(d,q,t,u,k);assert a.shape==b.shape and np.array_equal(a,b),(s,e,t,u,k)
  hashes.append(ahash(a))
 return hashes


def check_lineage(c,d,old,new):
 p=positions(c,[0,c.header[4],*[i for w in old for i in w]]);q=positions(d,[0,d.header[4],*[i for w in new for i in w]])
 assert registers(c)==registers(d)
 for k in (10,11):
  a,n=c.sections[k];b,m=d.sections[k];assert bytes(c.raw[a:a+n])==bytes(d.raw[b:b+m])
 gaps=[];last0=last1=0
 for (s,e),(t,u) in zip(old,new):
  hashes=same(c,p,last0,s,d,q,last1,t)
  gaps.append(dict(old=[last0,s],new=[last1,t],column_sha256=hashes));last0,last1=e,u
 hashes=same(c,p,last0,c.header[4],d,q,last1,d.header[4]);gaps.append(dict(old=[last0,c.header[4]],new=[last1,d.header[4]],column_sha256=hashes))
 return p,q,gaps


def write_spliced(source,source_positions,patches,destination,num_bits):
 chunks={k:[] for k in range(1,10)};last=0
 for start,end,donor,dp,ds,de in patches:
  assert start>=last
  for k in chunks:
   chunks[k].append(piece(source,source_positions,last,start,k));chunks[k].append(piece(donor,dp,ds,de,k))
  last=end
 for k in chunks:chunks[k].append(piece(source,source_positions,last,source.header[4],k))
 h=source.header.copy();h[2]=num_bits
 for hi,k in ((4,1),(5,2),(6,5),(7,7),(8,8),(9,9)):h[hi]=sum(len(v) for v in chunks[k])
 with Path(destination).open('wb') as f:
  f.write(source.raw[:16]);f.write(struct.pack('<4I9Q',*h))
  for p,n in source.regs:f.write(memoryview(source.raw)[p:p+n])
  for k in range(1,10):
   f.write(struct.pack('<QQ',k,sum(v.nbytes for v in chunks[k])))
   for a in chunks[k]:f.write(a)
  for k in (10,11):
   p,n=source.sections[k];f.write(struct.pack('<QQ',k,n));f.write(memoryview(source.raw)[p:p+n])
 return h


def emit_native(path,gates,nq,nb,magic):
 nq=1+max(q for g in gates for q in g['q'])
 cols={k:[]for k in range(1,10)}
 for g in gates:
  op=g['op'];cols[1].append(op);cat=(op&48)>>4
  for k,q in zip({0:[],1:[7],2:[5,6],3:[2,3,4]}[cat],g['q']):cols[k].append(q)
  if op&64:cols[8].append(g['bit'])
  if op&128:cols[9].append(g['cond'])
 arr={k:np.asarray(v,dtype=np.uint8 if k==1 else '<u4')for k,v in cols.items()}
 h=[2,nq,nb,0,len(arr[1]),len(arr[2]),len(arr[5]),len(arr[7]),len(arr[8]),len(arr[9]),0,0,0]
 with path.open('wb')as f:
  f.write(magic);f.write(struct.pack('<4I9Q',*h))
  for k,a in arr.items():f.write(struct.pack('<QQ',k,a.nbytes));f.write(a)
  f.write(struct.pack('<QQ',10,0));f.write(struct.pack('<QQ',11,8));f.write(bytes(8))
