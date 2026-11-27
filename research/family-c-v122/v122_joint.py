"""V122 isolated MAIN; run in the PR189 reproduction archive directory."""
import copy,json
from pathlib import Path
import donor_joint36_v2 as D
M=D.M

def recover23(c,v,p,z):
 c.cx(v[3],z);c.cx(v[4],z)
 c.cx(v[3],v[2]);c.cx(v[4],v[2]);c.cx(p,v[5])
 c.ccx(v[2],v[5],v[4]);c.cx(v[4],z)
 c.cx(p,v[3]);c.ccx(v[4],v[3],z);c.cx(p,v[3])
 c.ccx(v[2],v[5],v[4])
 c.cx(p,v[5]);c.cx(v[4],v[2]);c.cx(v[3],v[2])

def recover22(c,v,p,z):
 ws=v[1:]+[p];gs=M.chart_gates()
 for a,b in gs:c.cx(ws[a],ws[b])
 for i in range(6):
  if 62>>i&1:c.x(ws[i])
 a,b,u,d,e,f=ws
 c.x(b);c.cx(b,z);c.x(d);t=c.and_compute(e,d);c.x(d)
 c.cx(b,t);c.cx(f,t);c.ccx(u,t,z);c.cx(f,t);c.cx(b,t)
 c.x(d);c.and_erase(e,d,t);c.x(d);c.x(b)
 t=c.and_compute(a,d)
 c.cx(t,e);c.ccx(b,e,t)
 c.ccx(f,t,z);c.ccx(b,e,t);c.cx(t,e);c.and_erase(a,d,t)
 for i in range(6):
  if 62>>i&1:c.x(ws[i])
 for a,b in reversed(gs):c.cx(ws[a],ws[b])

if __name__=='__main__':
 import kickmix as km, numpy as np
 M.xor_recover23=recover23;M.xor_recover22=recover22
 b=M.build(36,True,False);c,U,v,F,word,nf,fp=b
 print('builder',c.next,c.peak,c.toffolis_exp(),len(c.ops),flush=True)
 assert c.next==36 and c.toffolis_exp()==431.5
 idx=np.unique(np.r_[np.arange(1024),np.random.default_rng(28).integers(0,len(M.T.U),8192)])
 for s in [0,1,28]:
  r=M.check(b,idx,s);print('sample',s,r,flush=True);assert not any(r.values())
 fw=copy.copy(c);fw.ops=c.ops[:nf]
 for name,a in [('v122_joint',c),('v122_joint_forward',fw)]:
  p=Path(name+'.kmx');p.write_text(M.K.kmx_text(a,list(range(31))));cc=km.Circuit.from_file(str(p));cc.to_file(name+'.kmb',format='kmb')
 Path('v122_joint_meta.json').write_text(json.dumps(dict(word=word,U=U,v=v,F=F,expected_paid=c.toffolis_exp()),indent=2))
