"""Replace only DQI in a pinned 18-member research archive."""
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path
from shutil import copyfileobj
from hashlib import file_digest
import sys,json
BASE='7d9fd29a849a1d10f76df81661f0cf7ad87f0345278397605581836284f87b68'
DONOR='b9f72a7bde001b81e0dc2530618dfa29815038b0bec7a542f75b2e3298d26870'
FILES={'dqi.kmb','invsqrt.kmb','dfthcsos/submission.npz'}|{f'dfthcsos/angle_k_{i}.kmb' for i in range(15)}
def sha(p):
 with open(p,'rb') as f:return file_digest(f,'sha256').hexdigest()
def contents(z):
 r={}
 for n in z.namelist():
  with z.open(n) as f:r[n]=file_digest(f,'sha256').hexdigest()
 return r
def main(base,donor,out):
 assert sha(base)==BASE and sha(donor)==DONOR
 out=Path(out)
 with ZipFile(base) as old, ZipFile(out,'x',compression=ZIP_DEFLATED,compresslevel=6) as z:
  assert len(old.namelist())==18 and set(old.namelist())==FILES
  before=contents(old)
  for n in old.namelist():
   if n=='dqi.kmb':src=open(donor,'rb')
   else:src=old.open(n)
   with src,z.open(n,'w',force_zip64=True) as f:copyfileobj(src,f,2**20)
 with ZipFile(out) as z:
  assert z.testzip() is None and len(z.namelist())==18 and set(z.namelist())==FILES
  after=contents(z)
 assert after['dqi.kmb']==DONOR and [n for n in before if before[n]!=after[n]]==['dqi.kmb']
 print(json.dumps(dict(archive_sha256=sha(out),members=after,unchanged=17,selected_dqi=DONOR,
                       research_only=True,official_score=None),indent=2))
if __name__=='__main__':main(*sys.argv[1:])
