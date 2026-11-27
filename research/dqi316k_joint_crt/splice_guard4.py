"""Replace both complete #237 phase-scan regions of exact #238 full tape.
Verify opcode and every physical operand map; no host selection.
CLI: python splice_guard4.py PARENT OLD237 NEW241 OUT
Requires append_hermite.py and splice237.py from the #238 source archive
in the same directory. The first four paths are explicit rather than
depending on the temporary experiment directory.
"""
from pathlib import Path
import numpy as np,sys,json,hashlib,struct
from append_hermite import KMB
src=Path(__file__).with_name('splice237.py').read_text()
exec(src[src.index('def offsets('):src.index('# At original scan boundary')])
parent,old,new=map(KMB,sys.argv[1:4]);output=sys.argv[4]
assert parent.count[0]==194317697 and old.count[0]==17917828 and new.count[0]==18282283
lo,hi=230260,17687568;nhi=hi+new.count[0]-old.count[0]
assert np.array_equal(np.frombuffer(old.view(1),np.uint8)[:lo],np.frombuffer(new.view(1),np.uint8)[:lo]);assert np.array_equal(np.frombuffer(old.view(1),np.uint8)[hi:],np.frombuffer(new.view(1),np.uint8)[nhi:])
O=Piece(old,lo,hi);N=Piece(new,lo,nhi)
def column(p,t):return np.frombuffer(p.k.view(t),'<u4')[p.start[t-1]:p.start[t-1]+p.n[t-1]]
pat=bytes(old.view(1)[lo:hi]);base=parent.p[1][0];end=base+parent.count[0];pos=base;found=[]
while True:
 pos=parent.d.find(pat,pos,end)
 if pos<0:break
 found.append(pos-base);pos+=len(pat)
print('hits',found,flush=True);assert len(found)==2
parts=[];last=0;receipt=[];fresh=parent.B
class NewScan(Piece):
 def __init__(self,q,cm,origin):super().__init__(new,lo,nhi,q=q);self.cm=cm;self.origin=origin
 def stream(self,t,f):
  if t<8:return super().stream(t,f)
  x=column(self,t)
  for st in range(0,len(x),1<<20):
   z=x[st:st+(1<<20)];f.write(self.cm[z].astype('<u4',copy=False).tobytes())
def bind(dst,a,b):
 assert len(a)==len(b)
 for st in range(0,len(a),1<<20):
  x=a[st:st+(1<<20)];y=b[st:st+(1<<20)];dst[x]=y;assert np.array_equal(dst[x],y)
for loc in found:
 old_parent=Piece(parent,loc,loc+len(pat));q=np.full(old.Q,0xffffffff,dtype='<u4');cm0=np.full(old.B,0xffffffff,dtype='<u4')
 for t in range(2,10):bind(q if t<8 else cm0,column(O,t),column(old_parent,t))
 for t in range(2,10):
  v=q if t<8 else cm0;assert np.array_equal(v[column(O,t)],column(old_parent,t)),t
 assert len(set(q[q!=0xffffffff]))==int(np.count_nonzero(q!=0xffffffff));assert len(set(cm0[cm0!=0xffffffff]))==int(np.count_nonzero(cm0!=0xffffffff))
 cm=np.full(new.B,0xffffffff,dtype='<u4');cm[:49140]=cm0[:49140];cm[49140:]=np.arange(fresh,fresh+new.B-49140,dtype='<u4')
 for t in range(2,10):
  v=q if t<8 else cm;assert np.all(v[column(N,t)]!=0xffffffff),t
 parts.extend([Piece(parent,last,loc),NewScan(q,cm,fresh),Clear(fresh,fresh+new.B-49140)])
 receipt.append({'parent_range':[loc,loc+len(pat)],'old_ops':O.count[0],'old_paid':O.count[1],'new_ops':N.count[0],'new_paid':N.count[1],'physical_Q_wires':int(np.count_nonzero(q!=0xffffffff)),'new_private_bits':new.B-49140})
 fresh+=new.B-49140;last=loc+len(pat)
parts.append(Piece(parent,last));out=emit(output,parent,parent.Q,fresh,parts)
res=dict(scope='full #238 physical splice; not submission',sha256=hashlib.file_digest(open(output,'rb'),'sha256').hexdigest(),Q=out.Q,ops=out.count[0],static_paid=out.count[1],old_static_paid=parent.count[1],seams=receipt);print(json.dumps(res),flush=True);Path(output+'.json').write_text(json.dumps(res,indent=2)+'\n')
