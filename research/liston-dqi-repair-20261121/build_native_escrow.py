"""Exact coherent flag checkpointing, with all slots and original HMR bits retained."""
import sys,json,struct
from pathlib import Path
from portable_native import Native,positions,piece,sha,check_lineage
import numpy as np
if len(sys.argv) != 3:
    raise SystemExit('Usage: python build_native_escrow.py source.kmb output.kmb')
source, dest = map(Path, sys.argv[1:])
if dest.exists():
    raise FileExistsError(dest)
expected='3c03fa53dd86be8e2ea3caa5d37597d371bc49426605a57a6ae8d31adc3c2ef3'
assert sha(source)==expected
c=Native(source)
assert c.header[0:2]==[2,889]
# forward HMR source op, qubit, outcome bit, reverse reconstruction op
sites=[(12812258,879,50425,49705732),(13121381,874,50570,49116710),
       (13459630,879,50715,48498528),(13837945,874,50860,47840476),
       (14229238,879,51005,47169458),(14668073,874,51150,46451090),
       (15130136,879,51295,45708316),(15160212,874,51439,45407557)]
p=positions(c,[0,c.header[4],*(j for f,q,b,r in sites for j in (f,f+1,r,r+1,r+2))])
def get(s,k):return int(c.a[k][p[s][0][k-1]])
patches={}; pair_audit=[]
for i,(f,q,b,r) in enumerate(sites):
 assert [get(f,k) for k in (1,7,8)]==[0x50,q,b],(i,[get(f,k) for k in (1,7,8)])
 assert get(r,1)==0x31 and get(r+1,1)==0x90,(i,hex(get(r,1)),hex(get(r+1,1)))
 target=get(r,4)
 assert get(r+1,7)==target and get(r+1,9)==b
 assert p[f][1]==p[r][1]==0
 e=889+i
 patches[f]=(f,{1:[0x21],5:[q],6:[e]})
 patches[r]=(r+1,{1:[0x22],5:[e],6:[target]})
 pair_audit.append(dict(slot=17+2*i,forward_hmr=f,forward_q=q,x_measure_bit=b,
                        reverse_ccx=r,restore_q=target,escrow_q=e))
last=length=0; chunks={k:[] for k in range(1,10)}; old=[];new=[]
for start,(end,cols) in sorted(patches.items()):
 assert last<=start
 old.append((start,end)); length+=start-last
 new.append((length,length+1)); length+=1
 for k in chunks:
  chunks[k].append(piece(c,p,last,start,k))
  if k in cols:chunks[k].append(np.asarray(cols[k],dtype=np.uint8 if k==1 else '<u4'))
 last=end
for k in chunks:chunks[k].append(piece(c,p,last,c.header[4],k))
h=c.header.copy()
h[1]=897
for hi,k in ((4,1),(5,2),(6,5),(7,7),(8,8),(9,9)):h[hi]=sum(len(v) for v in chunks[k])
assert [h[i]-c.header[i] for i in range(13)]==[0,8,0,0,8,-8,16,0,0,0,0,0,0]
tmp=dest.with_suffix('.part')
with tmp.open('wb')as out:
 out.write(c.raw[:16]);out.write(struct.pack('<4I9Q',*h))
 for off,n in c.regs:out.write(memoryview(c.raw)[off:off+n])
 for k in chunks:
  out.write(struct.pack('<QQ',k,sum(v.nbytes for v in chunks[k])))
  for a in chunks[k]:out.write(a)
 for k in (10,11):
  off,n=c.sections[k];out.write(struct.pack('<QQ',k,n));out.write(memoryview(c.raw)[off:off+n])
d=Native(tmp)
_,_,gaps=check_lineage(c,d,old,new)
digest=sha(tmp)
tmp.replace(dest)
receipt=dict(source_sha256=expected,patched_sha256=digest,source_header=c.header,new_header=h,pairs=pair_audit,untouched_column_regions=gaps)
dest.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='untouched_column_regions'},indent=2))
