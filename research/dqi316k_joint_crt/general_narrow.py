"""Reuse masked numerator workspace for the guarded phase16 computation.
The 12 masked-numerator bits are erased before the inner kernel and
recomputed for exact HMR repayment. All the extra operations are Clifford.
"""
import general_scan as S, crt882 as C, joint_phase as J
import kickmix as km
import argparse,hashlib,json
from pathlib import Path
def narrow_kernel(b,f,d,p,work,mask):
 chain=work[:11]; n=work[11:17]; c=work[17:23];shared=work[23:39]
 up=shared[:12]; g=shared[:6]; w=shared[6:16]
 S.root(b,f,chain);r=chain[-1]
 S.masked(b,p,mask,up)
 J.frame(b,d,C.BASIS12,True);a,bb=d[:6],d[6:];u,v=up[:6],up[6:]
 left=a+u;right=bb+v
 S.compute_tensor(b,left,right,n+c)
 sa=[S.gf(1<<i,1<<i) for i in range(6)];sb=[S.gf(C.K6,x) for x in sa]
 J.arith(b,'square',a,n,1,6,0x43);J.arith(b,'square',bb,n,C.K6,6,0x43)
 S.masked(b,p,mask,up)
 for x,y in zip(c,g):b.ccx(r,x,y)
 S.phase16(b,n,g,w)
 for x,y in zip(c,g):b.del_and(r,x,y)
 S.masked(b,p,mask,up)
 mb=J.measure(b,n+c);S.repay_tensor(b,left,right,mb);J.linearphase(b,a,mb[:6],sa);J.linearphase(b,bb,mb[:6],sb);J.cclear(b,mb)
 J.frame(b,d,C.BASIS12);S.masked(b,p,mask,up);S.unroot(b,f,chain)
def main():
 p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=4095);p.add_argument('--cases',type=int,default=4);a=p.parse_args()
 import inspect
 src=inspect.getsource(S.make).replace('alloc_qubits(51)','alloc_qubits(39)')
 S.Q=879;S.kernel=narrow_kernel;exec(src,S.__dict__)
 S.exact_tensor()
 c=S.make(a.count);f=Path(f'general_narrow_{a.count}.kmb');c.to_file(str(f),format='kmb');del c
 c=km.Circuit.from_file(str(f));r=dict(scope='canonical general rational phase only, no syndrome decoder',Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),scan_points=a.count)
 print(json.dumps(r),flush=True);r.update(S.test(c,a.count,a.cases));print(json.dumps(r),flush=True);f.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');assert not any(r['errors'])
if __name__=='__main__':main()
