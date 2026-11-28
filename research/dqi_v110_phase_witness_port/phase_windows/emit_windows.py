"""Emit reversible product-window coupons using #246 and spectral rank_run.

Inputs are certified field coordinates placed in the physical #261 seam.
Read-only coefficient registers and arbitrary dirty accumulators are preserved
except for the requested XOR, with all 35 nominal free qubits untouched.
"""
from pathlib import Path
import json,sys
src=Path(sys.argv[1]).read_text()
spec=Path(sys.argv[2]).read_text()
l=json.loads(Path(sys.argv[3]).read_text())['layout']
assert len({i for v in l['D']+l['N'] for i in v})==852
for w in l['D']+l['N']:
    assert w==list(range(w[0],w[0]+12)),w
D,N=([v[0] for v in l[k]] for k in ('D','N'))
with Path('seam_layout.inc').open('w') as f:
    for k,v in [('Dword',D),('Nword',N)]:
        print('const Words '+k+'={'+','.join(map(str,v))+'};',file=f)
src=src[:src.index("void magnitude(){")]+spec[spec.index("void rank_run("):]
src=src.replace('Q=851,FLAG=49140,HM=49141','Q=900,FLAG=0,HM=0')
src=src.replace('2*N+M};','1};')
src=src.replace('HM+1,1};','0,1};')
a=src.index('for(int i=0;i<N;i++)reg')
b=src.index('for(U k=1;',a)
src=src[:a]+'''{string label="seam";U kind=0,size=8+label.size()+4*Q;I n=label.size(),r=Q;
 f.write((char*)&kind,8);f.write((char*)&size,8);f.write((char*)&n,4);f.write((char*)&r,4);f.write(label.data(),n);
 for(I i=0;i<Q;i++){I w=i|0x80000000;f.write((char*)&w,4);}}'''+src[b:]
src=src.replace('cout<<name<<" Q="','{U t=10,n=0;f.write((char*)&t,8);f.write((char*)&n,8);t=11;n=8;f.write((char*)&t,8);f.write((char*)&n,8);n=0;f.write((char*)&n,8);}cout<<name<<" Q="')
Path('windows.cpp').write_text(src+Path(__file__).with_name('windows.cpp.inc').read_text())
