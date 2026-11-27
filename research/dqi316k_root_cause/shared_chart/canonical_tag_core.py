"""Native canonical pad-scale XOR decoder on supplied 70-word locator/magnitude ABI.
Core generator used by the independent KickMix tests in the joint-fusion archive.
Dependencies: direct_codec, chart_selector, pole_helpers, test_extension_padding
and the fixed extension_padding_receipt.json from the previous #227 archive.
Not a claim that the frozen donor exposes this ABI.
"""
import json
import kickmix as km
from chart_selector import mat_ops
from pole_helpers import ep,ei
from test_extension_padding import em
from pathlib import Path

def run_ops(b,ops,rev=False):
 for op,a,c in (reversed(ops) if rev else ops):getattr(b,op)(a,c)
def frame(data,cols,n):
 rows=[sum(((v>>i)&1)<<j for j,v in enumerate(cols)) for i in range(n)]
 r=rows.copy();pv=[]
 for j in range(len(data)):
  i=next((i for i in range(len(pv),n) if r[i]>>j&1),None)
  if i is None:continue
  k=len(pv);r[i],r[k]=r[k],r[i]
  for i in range(n):
   if i!=k and r[i]>>j&1:r[i]^=r[k]
  pv.append(j)
  if len(pv)==n:break
 assert len(pv)==n
 q=[data[j] for j in pv]
 a=tuple(sum(((row>>j)&1)<<i for i,row in enumerate(rows)) for j in pv)
 ops=[(op,q[i],q[j]) for op,i,j in mat_ops(a)];ps=set(pv)
 for i,row in enumerate(rows):
  for j in range(len(data)):
   if j not in ps and row>>j&1:ops.append(('cx',data[j],q[i]))
 return q,ops

def build(mode,pad_receipt):
 assert mode in ('known_low','conditional_clean','conditional_dirty')
 roots=json.loads(Path(pad_receipt).read_text())['pads'][0]['roots']
 c,_,e=roots[0];z=c|4096;ie=ei(e);Z=[];w=1
 for _ in range(36):Z.append(w);w=em(w,z)
 b=km.CircuitBuilder();p=list(b.create_quantum_register(420,'locator35'));v=list(b.create_quantum_register(420,'magnitude35'));tag=list(b.create_quantum_register(2,'tag'))
 Pcols=[em(Z[j],1<<k) for j in range(35) for k in range(12)]
 Vcols=[em(ie,em(Z[j],1<<k))&3 for j in range(35) for k in range(12)]
 vb,vo=frame(v,Vcols,2);run_ops(b,vo)
 if mode=='known_low':
  for x,y in zip(vb,tag):b.cx(x,y)
 else:
  pb,po=frame(p,Pcols,24);run_ops(b,po)
  for k,q in enumerate(pb):
   if not Z[35]>>k&1:b.x(q)
  if mode=='conditional_clean':
   a=list(b.alloc_qubits(23))
   chain=[(pb[0],pb[1],a[0])]+[(a[j-1],pb[j+1],a[j]) for j in range(1,23)]
   for x,y,t in chain:b.ccx(x,y,t)
   for x,y in zip(vb,tag):b.ccx(a[-1],x,y)
   for x,y,t in reversed(chain):b.del_and(x,y,t)
   b.free(a)
  else:
   f=b.alloc_qubits(1)[0];d=[x for x in v if x not in vb][:22];n=len(pb)
   chain=[(pb[0],pb[1],d[0])]+[(d[j-1],pb[j+1],d[j]) for j in range(1,n-2)]
   def toggle():
    for l in (chain,chain[1:]):
     for x,y,t in l:b.ccx(x,y,t)
     b.ccx(d[-1],pb[-1],f)
     for x,y,t in reversed(l):b.ccx(x,y,t)
   toggle()
   for x,y in zip(vb,tag):b.ccx(f,x,y)
   toggle();b.free([f])
  for k,q in enumerate(pb):
   if not Z[35]>>k&1:b.x(q)
  run_ops(b,po,True)
 run_ops(b,vo,True);return b.finish_circuit()

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('mode',choices=('known_low','conditional_clean','conditional_dirty'));a.add_argument('pad_receipt');a.add_argument('output');p=a.parse_args()
 c=build(p.mode,p.pad_receipt);c.to_file(p.output,format='kmb');print(c.num_qubits,len(c),c.operation_statistics().num_toffoli_like)
