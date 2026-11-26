"""Native coherent21-bit address-constant adder using low-word carry pebbling.
Keep the five high-word lines clean during modular low16 addition; populate
high=constant_high+[sum_low<constant_low] afterwards. No rounding bit is lost.
"""
from pathlib import Path
import sys,json,time,hashlib,heapq,functools
from collections import Counter
import numpy as np
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[1]/'port31'
sys.path.insert(0,str(PORT))
import coherent_horner as H
from emit_meet import NativeKMB,Op
from small_multiplier import Bld

LOW=H.WORD[:16];HIGH=H.WORD[16:];FLAG=H.FLAG

@functools.lru_cache(None)
def increment_plan(n,cap):
 # State=(next bit to toggle, available old-prefix carry nodes).
 # A carry C_j=f*prod_{i<j}x_i may be erased while its predecessor exists.
 # Bit k may be changed only when all carry nodes >k have been erased.
 start=(n-1,0);goal=(-1,0);dist={start:0};prev={};heap=[(0,start)]
 while heap:
  cost,st=heapq.heappop(heap)
  if cost!=dist.get(st):continue
  if st==goal:break
  k,m=st;actions=[]
  if k>=0 and (k==0 or m>>(k-1)&1) and (m>>k)==0:
   actions.append(((k-1,m),('toggle',k),1))
  for j in range(1,n):
   bit=1<<(j-1);pred=(j==1 or m>>(j-2)&1)
   if not pred:continue
   if m&bit:actions.append(((k,m^bit),('erase',j),4))
   elif j<=k and m.bit_count()<cap:actions.append(((k,m|bit),('compute',j),10000+1))
  for ns,a,w in actions:
   nd=cost+w
   if nd<dist.get(ns,10**20):dist[ns]=nd;prev[ns]=(st,a);heapq.heappush(heap,(nd,ns))
 else:raise RuntimeError(('unreachable increment',n,cap))
 out=[];st=goal
 while st!=start:st,a=prev[st];out.append(a)
 out.reverse();return tuple(out)

@functools.lru_cache(None)
def comparator_plan(depth,cap):
 if depth==0:return ()
 start=(0,False);goal=(0,True);dist={start:0};prev={};heap=[(0,start)]
 while heap:
  cost,st=heapq.heappop(heap)
  if cost!=dist.get(st):continue
  if st==goal:break
  m,done=st
  for j in range(1,depth+1):
   bit=1<<(j-1)
   if j!=1 and not(m>>(j-2)&1):continue
   if m&bit:ns=(m^bit,done);a=('erase',j);w=4
   elif m.bit_count()<cap:ns=(m|bit,done or j==depth);a=('compute',j);w=10001
   else:continue
   nd=cost+w
   if nd<dist.get(ns,10**20):dist[ns]=nd;prev[ns]=(st,a);heapq.heappush(heap,(nd,ns))
 else:raise RuntimeError(('unreachable comparator',depth,cap))
 out=[];st=goal
 while st!=start:st,a=prev[st];out.append(a)
 out.reverse();return tuple(out)


def conditional_increment(b,word,seed,free,sign):
 if sign<0:
  for q in word:b.X(q)
 where={0:seed}
 for kind,j in increment_plan(len(word),len(free)):
  if kind=='toggle':b.CX(where[j],word[j]);continue
  if kind=='compute':
   t=next(q for q in free if q not in where.values());b.CCX(where[j-1],word[j-1],t);where[j]=t
  else:b.erase(where.pop(j),[where[j-1],word[j-1]])
 assert where=={0:seed}
 if sign<0:
  for q in reversed(word):b.X(q)


def add_low(b,negative=False):
 groups={}
 for a,k in enumerate(H.CONSTANT):
  for j,d in H.naf(int(k)):
   if j<16:groups[j,d]=groups.get((j,d),0)|(1<<a)
 events=[(mask,j,-d if negative else d)for (j,d),mask in sorted(groups.items(),reverse=not negative)]
 old=0
 for mask,j,d in events:
  b.add(*H.flag_ops(old^mask));old=mask
  conditional_increment(b,LOW[j:],FLAG,HIGH,d)
 b.add(*H.flag_ops(old))


def compare_constant(b,k,out,seed,free):
 # [x<k]=k15*C0 XOR sum_j(k_{16-j} XOR k_{15-j})*Cj XOR k0*C16.
 # Ci=seed*[first i high input bits equal the constant prefix].
 bits=[(k>>(15-i))&1 for i in range(16)]
 want={j for j in range(1,16) if bits[j-1]!=bits[j]}
 last=bool(bits[-1]);depth=max(want|({15}if last else {0}))
 if bits[0]:b.CX(seed,out)
 where={0:seed};visited=set()
 for kind,j in comparator_plan(depth,len(free)):
  q=LOW[16-j]
  if not bits[j-1]:b.X(q)
  if kind=='compute':
   t=next(q for q in free if q not in where.values());b.CCX(where[j-1],q,t);where[j]=t
  else:b.erase(where.pop(j),[where[j-1],q])
  if not bits[j-1]:b.X(q)
  if kind=='compute' and j not in visited:
   visited.add(j)
   if j in want:b.CX(where[j],out)
   if j==15 and last:b.CCX(where[j],LOW[0],out)
 assert where=={0:seed} and want<=visited


def carry(b):
 old=0
 for a,k in enumerate(H.CONSTANT):
  low=int(k)&65535
  if low==0:continue
  mask=1<<a;b.add(*H.flag_ops(old^mask));old=mask
  compare_constant(b,low,HIGH[0],FLAG,HIGH[1:])
 b.add(*H.flag_ops(old))


def high_extension(b,negative=False):
 hi=[int(k)>>16 for k in H.CONSTANT];delta=[(k^(k+1))&31 for k in hi];events=[]
 for j in range(1,5):
  mask=sum(1<<a for a,k in enumerate(hi)if k>>j&1)
  events.append((mask,Op(33,(FLAG,HIGH[j]))))
  mask=sum(1<<a for a,k in enumerate(delta)if k>>j&1)
  events.append((mask,Op(49,(HIGH[0],FLAG,HIGH[j]))))
 mask=sum(1<<a for a,k in enumerate(hi)if k&1);events.append((mask,Op(33,(FLAG,HIGH[0]))))
 if negative:events.reverse()
 old=0
 for mask,op in events:
  if not mask:continue
  b.add(*H.flag_ops(old^mask),op);old=mask
 b.add(*H.flag_ops(old))


def main(tag=""):
 start=time.time();base=NativeKMB.read(H.SRC/'v61_pipeline_p1_r1_Q36_PARTIAL.kmb');meta=json.load(open(H.SRC/'v61_pipeline_p1_r1_receipt.json'));old=meta['snapshot']
 b=Bld(base.header[2]);stats={}
 for name,func in [('low',add_low),('carry',carry),('high',high_extension)]:
  p=len(b.ops);func(b);stats[name]={'ccx':sum(o.raw==49 for o in b.ops[p:]),'ops':len(b.ops)-p}
 forward=b.ops[:];b.ops=[]
 high_extension(b,True);carry(b);add_low(b,True);inverse=b.ops[:]
 ops=base.ops[:old]+forward+inverse+base.ops[old:];hdr=list(base.header);hdr[2]=b.m
 C=NativeKMB(base.prefix16,tuple(hdr),base.sections,ops);out=HERE/('coherent_first_horner_split_carry'+tag+'_Q36_PARTIAL.kmb');out.write_bytes(C.to_bytes());C=NativeKMB.read(out)
 c=Counter(o.raw for o in C.ops);r={'scope':'complete coherent first-Horner chart roundtrip only; not31R full invsqrt','Q':36,'ccx':c[49],'expected_paid':c[49]+0.5*c[176],'instructions':len(C.ops),'hmr':c[80],'rotations':c[19],'forward_ccx':sum(o.raw==49 for o in forward),'inverse_ccx':sum(o.raw==49 for o in inverse),'forward_instructions':len(forward),'snapshot':old+len(forward),'original_snapshot':old,'stages':stats,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
 print('EMITTED',r,flush=True)
 r['verification']=H.verify_whole(C,r['snapshot'],old);r['seconds']=time.time()-start
 (HERE/('split_carry'+tag+'_receipt.json')).write_text(json.dumps(r,indent=2));print('PASS',r,flush=True)
 (HERE/'increment_pebble_counts.json').write_text(json.dumps({str(n):{'ccx':sum(a=='compute' for a,j in increment_plan(n,5)),'actions':len(increment_plan(n,5))}for n in range(1,17)},indent=2))

if __name__=='__main__':main()
