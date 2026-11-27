import ctypes as C,sys,numpy as np,hashlib,struct,json,collections
from pathlib import Path
import kmb
R=Path(sys.argv[1]);src=R/'fused510/dqi.kmb';c=kmb.read(str(src))
assert hashlib.file_digest(src.open('rb'),'sha256').hexdigest()=='5f263701fa455a429c06a75f8d994e9ec1465cff69467d7a81ef00b3a68b30a8'
d=np.zeros(len(c.ops),np.uint8);f=C.CDLL(str(Path(sys.argv[2]).resolve())).scan
P=C.c_void_p;L=C.c_int64;I=C.c_int
f.argtypes=[P,L]+[P]*8+[I,I]+[L]*5+[P,C.c_char_p];f.restype=None
args=[c.ops.ctypes.data,len(c.ops)]+[a.ctypes.data for a in c.q3+c.q2+(c.q1,c.bit_t,c.cond)]+[c.num_qubits,c.num_bits,len(c.q1),len(c.q2[0]),len(c.q3[0]),len(c.bit_t),len(c.cond),d.ctypes.data,str(R/'deadwrite.txt').encode()]
f(*args)
ins=collections.defaultdict(list)
for line in (R/'deadwrite.txt').read_text().splitlines():
 i,r,a,b,h=map(int,line.split());assert d[i]==2 and c.ops[i]==49 and c.ops[r]==80 and d[r]==0;ins[r].append((a,b,h))
p=R/'fused510_rewrite.kmb';data=np.memmap(src,dtype=np.uint8,mode='r');pos=104;packets=[]
while pos<len(data):
 typ,ln=struct.unpack('<QQ',data[pos:pos+16]);off=pos+16;packets.append((typ,off,ln));pos=off+ln
ops=c.ops;keep=d==0;cls=(ops&48)>>4;bit=((ops&64)!=0)&((ops&127)!=6)&((ops&127)!=7);cond=(ops&128)!=0
positions=np.array(sorted(ins),np.int64);rep=np.array([len(ins[x]) for x in positions]);nnew=int(rep.sum());assert nnew==np.count_nonzero(d==2)
add_a=np.array([a for x in positions for a,b,h in ins[x]],dtype='<u4');add_b=np.array([b for x in positions for a,b,h in ins[x]],dtype='<u4');add_h=np.array([h for x in positions for a,b,h in ins[x]],dtype='<u4')
def merge(a,idx,vals):
 out=np.empty(len(a)+len(vals),dtype=a.dtype);prev=outp=vp=0
 for t,count in zip(idx,rep):
  l=int(t)-prev;out[outp:outp+l]=a[prev:t];outp+=l;out[outp:outp+count]=vals[vp:vp+count];vp+=count;outp+=count;prev=int(t)
 out[outp:]=a[prev:];return out
def at(m):
 cuts=np.r_[0,positions+1];return np.cumsum([np.count_nonzero(m[a:b]) for a,b in zip(cuts[:-1],cuts[1:])])
newops=merge(ops[keep],at(keep),np.full(nnew,0xA0,np.uint8))
counts=[len(newops),int(np.count_nonzero(keep&(cls==3))),int(np.count_nonzero(keep&(cls==2)))+nnew,int(np.count_nonzero(keep&(cls==1))),int(np.count_nonzero(keep&bit)),int(np.count_nonzero(keep&cond))+nnew,len(c.angles),len(c.tags),sum(len(t.encode()) for t in c.tags)]
arrs={2:(c.q3[0],cls==3),3:(c.q3[1],cls==3),4:(c.q3[2],cls==3),5:(c.q2[0],cls==2),6:(c.q2[1],cls==2),7:(c.q1,cls==1),8:(c.bit_t,bit),9:(c.cond,cond)}
with p.open('wb') as out:
 out.write(data[:32]);out.write(struct.pack('<9Q',*counts))
 for typ,off,ln in packets:
  if typ==1:a=newops
  elif typ in arrs:
   orig,m=arrs[typ];a=orig[keep[m]]
   if typ in (5,6,9):a=merge(a,at(keep&m),{5:add_a,6:add_b,9:add_h}[typ])
  else:
   out.write(struct.pack('<QQ',typ,ln));out.write(data[off:off+ln]);continue
  out.write(struct.pack('<QQ',typ,a.nbytes));out.write(a);del a
new=kmb.read(str(p));assert new.num_qubits==c.num_qubits and new.num_bits==c.num_bits
assert len(new.ops)==counts[0] and int(new.is_toffoli.sum())==int(c.is_toffoli.sum())-nnew
r={'source_sha256':hashlib.file_digest(src.open('rb'),'sha256').hexdigest(),'candidate_sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'source_ops':len(c.ops),'candidate_ops':len(new.ops),'source_static_paid':int(c.is_toffoli.sum()),'candidate_static_paid':int(new.is_toffoli.sum()),'cancelled_pairs':int(np.count_nonzero(d==1))//2,'dead_write_ccx_removed':nnew,'phase_cz_inserted':nnew,'width':c.num_qubits}
assert r['candidate_sha256']=='a50bf1ab908d344cb02c267b3af7d986da22d453e19448eee4e13af1c3d19cf5',r
(R/'rewrite_receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
