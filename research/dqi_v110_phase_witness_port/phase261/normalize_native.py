"""Cost and width of explicit projective normalization, not a full splice."""
import json,hashlib
from pathlib import Path
import numpy as np,kickmix as km
import crt882 as C

def build(roundtrip):
    # 71 data words and the existing #261 seam's 13 retained bits.
    b=km.CircuitBuilder();b.set_max_qubits(900)
    x=list(b.create_quantum_register(852,'DN'));keep=list(b.create_quantum_register(13,'retained'))
    w=list(b.alloc_qubits(30));xid=lambda i,*j: list(range(i,i+12))
    lead=xid(420); inv=xid(865);tmp=xid(877);sub=list(range(877,895))
    cc=C.Compact()
    cc.inv12(lead,inv,sub)
    for i in (*range(35),*range(36,71)):
        v=xid(12*i)
        cc.prod(v,inv,tmp,12,C.MOD)
        for a,t in zip(v,tmp):cc.cx(a,t);cc.cx(t,a);cc.cx(a,t)
        cc.prod(v,lead,tmp,12,C.MOD)
    cc.inv12(lead,inv,sub)
    ops=cc.ops+list(reversed(cc.ops)) if roundtrip else cc.ops
    q=x+keep+w
    for g,*args in ops:getattr(b,('x','cx','ccx')[g])(*(q[i] for i in args))
    p=Path('normalization_roundtrip.kmb' if roundtrip else 'normalization_forward.kmb')
    circ=b.finish_circuit();circ.to_file(str(p),format='kmb')
    return circ,p

def main():
    cases=[json.loads(x) for x in Path('raw_words.jsonl').read_text().splitlines()]
    def words(z):return ((np.asarray(z,np.uint16)[:,:,None]>>np.arange(12))&1).reshape(len(z),-1).T.astype(bool)
    rng=np.random.default_rng(3260);ans=[]
    for r in (False,True):
        circ,p=build(r); q=km.array([km.q(i) for i in range(852)]);keep=km.array([km.q(i) for i in range(852,865)]);scratch=km.array([km.q(i) for i in range(865,895)])
        ne=0
        for i in range(0,len(cases),64):
            cases1=cases[i:i+64];s0=[z[7]+z[8] for z in cases1];s1=[]
            for v in s0:
                c=v[35];assert c
                s1.append([C.m(x,C.inv(c)) if j!=35 else c for j,x in enumerate(v)])
            a=words(s0);want=words(s0 if r else s1);g=rng.integers(0,2,(13,len(cases1)),dtype=bool)
            sim=km.Simulator(batch_size=len(cases1),seed=7856,debug_print=False,counting_operations=True);sim.use_same_registers_as(circ);sim.write_across_shots(q,a);sim.write_across_shots(keep,g);sim.do(circ)
            ne+=int(np.logical_or.reduce([(sim.read_across_shots(q)!=want).any(0),(sim.read_across_shots(keep)!=g).any(0),sim.read_across_shots(scratch).any(0),sim.read_phase_flipped_across_shots()]).sum())
        row=dict(file=str(p),width=circ.num_qubits,ops=len(circ),CCX=int(circ.operation_statistics().num_toffoli_like),sha=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),cases=len(cases),errors=ne)
        print(row,flush=True);ans.append(row)
    Path('normalization_receipt.json').write_text(json.dumps(ans,indent=2)+'\n')
if __name__=='__main__':main()
