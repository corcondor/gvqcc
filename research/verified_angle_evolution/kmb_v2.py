"""Exact Kickmix v2 binary parser and serializer for circuit transformation tests."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct
from array import array
H=struct.Struct('<16s4I9Q');P=struct.Struct('<QQ')
MAGIC=bytes.fromhex('d750c7d5c329d326e3cc9f6834f2b8bf')
OPS={0x00:'NEG',0x01:'POP_CONDITION',0x10:'Z',0x11:'X',0x12:'R',0x13:'Z_POW',0x20:'CZ',0x21:'CX',0x22:'SWAP',0x30:'CCZ',0x31:'CCX',0x32:'CSWAP',0x40:'BIT_STORE0',0x41:'BIT_STORE1',0x42:'BIT_INVERT',0x50:'HMR',0x06:'INFO_TAG',0x07:'DEBUG_PRINT_EMPTY',0x47:'DEBUG_PRINT_C',0x17:'DEBUG_PRINT_Q',0x87:'DEBUG_PRINT_EMPTY_IF',0x97:'DEBUG_PRINT_Q_IF',0xc7:'DEBUG_PRINT_C_IF'}
OPS.update({k|128:v+'_IF' for k,v in list(OPS.items()) if k|128 not in OPS})
OP_CODES={v:k for k,v in OPS.items()}
OP_CODES['PUSH_CONDITION']=0x81
@dataclass
class Gate:
 op:int
 q:tuple[int,...]=()
 bit:tuple[int,...]=()
 cond:tuple[int,...]=()
 angle:bytes=b''
 @property
 def name(self):return 'PUSH_CONDITION' if self.op==0x81 else OPS.get(self.op,'UNKNOWN')

@dataclass
class Circuit:
 magic:bytes
 version:int
 nqubits:int
 nbits:int
 registers:list[tuple[bytes,tuple[int,...]]]
 ops:list[Gate]
 tags:list[bytes]
 def write(self,path):
  n3=sum(len(g.q)==3 for g in self.ops);n2=sum(len(g.q)==2 for g in self.ops);n1=sum(len(g.q)==1 for g in self.ops);nb=sum(len(g.bit)==1 for g in self.ops);nc=sum(len(g.cond)==1 for g in self.ops);na=sum(bool(g.angle) for g in self.ops)
  header=H.pack(self.magic,self.version,self.nqubits,self.nbits,len(self.registers),len(self.ops),n3,n2,n1,nb,nc,na,len(self.tags),sum(map(len,self.tags)))
  payloads=[]
  for name,ids in self.registers:payloads.append((0,struct.pack('<II',len(name),len(ids))+name+struct.pack('<'+'I'*len(ids),*ids)))
  payloads.append((1,bytes(g.op for g in self.ops)))
  for pkt,subset,index in [(2,3,0),(3,3,1),(4,3,2),(5,2,0),(6,2,1),(7,1,0)]:
   ids=[g.q[index] for g in self.ops if len(g.q)==subset]
   payloads.append((pkt,struct.pack('<'+'I'*len(ids),*ids)))
  for pkt,name in [(8,'bit'),(9,'cond')]:
   ids=[getattr(g,name)[0] for g in self.ops if len(getattr(g,name))==1]
   payloads.append((pkt,struct.pack('<'+'I'*len(ids),*ids)))
  payloads.append((10,b''.join(g.angle for g in self.ops if g.angle)))
  offs=[];val=0
  for s in self.tags:val+=len(s);offs.append(val)
  payloads.append((11,struct.pack('<Q',len(self.tags))+struct.pack('<'+'Q'*len(offs),*offs)+b''.join(self.tags)))
  result=bytearray(header)
  for k,p in payloads:result+=P.pack(k,len(p));result+=p
  Path(path).write_bytes(result)
  return bytes(result)

def load(path):
 data=Path(path).read_bytes();magic,ver,nq,nb,nr,nop,n3,n2,n1,nb1,ncond,nangle,ntag,nchar=H.unpack_from(data)
 assert magic==MAGIC and ver==2
 offset=H.size;regs=[];packets={}
 for j in range(nr+11):
  pk,size=P.unpack_from(data,offset);offset+=P.size;pay=memoryview(data)[offset:offset+size];offset+=size
  if j<nr:
   assert pk==0; nl,count=struct.unpack_from('<II',pay);name=bytes(pay[8:8+nl]);ids=struct.unpack_from('<'+'I'*count,pay,8+nl);regs.append((name,ids))
  else:
   assert pk==j-nr+1,(j,nr,pk);packets[pk]=pay
 assert offset==len(data),(offset,len(data))
 def u32s(num):
  arr=array('I');arr.frombytes(packets[num]);return iter(arr)
 q3=[u32s(i) for i in range(2,5)];q2=[u32s(i) for i in range(5,7)];q1=u32s(7);b0=u32s(8);bc=u32s(9);angles=memoryview(packets[10]);ia=0
 gates=[]
 for op in packets[1]:
  if op&0x30==0x30:q=tuple(next(itr) for itr in q3)
  elif op&0x30==0x20:q=tuple(next(itr) for itr in q2)
  elif op&0x30==0x10:q=(next(q1),)
  else:q=()
  b=(next(b0),) if op&0x40 else ()
  c=(next(bc),) if op&0x80 else ()
  a=bytes(angles[ia:ia+16]) if op&0x7f==0x13 else b''
  if a:ia+=16
  gates.append(Gate(op,q,b,c,a))
 assert ia==len(angles)
 tagdata=packets[11];nt=struct.unpack_from('<Q',tagdata)[0];assert nt==ntag
 ends=struct.unpack_from('<'+'Q'*nt,tagdata,8);body=bytes(tagdata[8+8*nt:]);tags=[];prev=0
 for j in ends:tags.append(body[prev:j]);prev=j
 return Circuit(magic,ver,nq,nb,regs,gates,tags)

if __name__=='__main__':
 import sys,hashlib
 c=load(sys.argv[1]);output=sys.argv[2] if len(sys.argv)>2 else '/tmp/kmb_roundtrip.kmb';b=c.write(output)
 original=Path(sys.argv[1]).read_bytes()
 print('ops',len(c.ops),'regs',[(r[0].decode(),len(r[1])) for r in c.registers], 'bytes',len(b),'roundtrip',b==original)
