"""HMR normalization using the existing GF tensor and measured product-phase repayment."""
import json,hashlib,sys
from pathlib import Path
import numpy as np,kickmix as km
sys.path.insert(0,'/tmp/seam')
import crt882 as C,joint_phase as J

def build(mode):
    b=km.CircuitBuilder();b.set_max_qubits(900)
    x=list(b.create_quantum_register(852,'DN'));keep=list(b.create_quantum_register(13,'retained'))
    w=list(b.alloc_qubits(30));lead=x[420:432]; inv=w[:12];tmp=w[12:24];sub=w[12:30]
    def invxor():
        cc=C.Compact();cc.inv12(list(range(12)),list(range(12,24)),list(range(24,42)))
        q=lead+inv+sub
        for g,*args in cc.ops:getattr(b,('x','cx','ccx')[g])(*(q[i] for i in args))
    def action(back):
        f,g=(lead,inv) if back else (inv,lead)
        for i in (*range(35),*range(36,71)):
            v=x[12*i:12*i+12]
            J.arith(b,'prod',v,f,tmp,12,C.MOD)
            for z,t in zip(v,tmp):b.swap(z,t)
            J.product_clear(b,v,g,tmp,12,C.MOD)
    invxor()
    if mode!='reverse':action(False)
    if mode!='forward':action(True)
    invxor()
    b.free(w)
    c=b.finish_circuit();p=Path('normalize_hmr_'+mode+'.kmb');c.to_file(str(p),format='kmb')
    return c,p

def main():
    cases=[json.loads(x) for x in Path('raw_words.jsonl').read_text().splitlines()]
    def words(z):return ((np.asarray(z,np.uint16)[:,:,None]>>np.arange(12))&1).reshape(len(z),-1).T.astype(bool)
    rng=np.random.default_rng(3260);ans=[]
    for mode in ('forward','reverse','roundtrip'):
        c,p=build(mode); q=km.array([km.q(i) for i in range(852)]);keep=km.array([km.q(i) for i in range(852,865)]);scratch=km.array([km.q(i) for i in range(865,895)])
        ne=shots=paid=0
        for i in range(0,len(cases),64):
            cases1=cases[i:i+64];s0=[z[7]+z[8] for z in cases1]
            s1=[[C.m(x,C.inv(v[35])) if j!=35 else v[35] for j,x in enumerate(v)]for v in s0]
            a=words(s1 if mode=='reverse' else s0);want=words(s1 if mode=='forward' else s0);g=rng.integers(0,2,(13,len(cases1)),dtype=bool)
            for seed in (7856,7857):
                s=km.Simulator(batch_size=len(cases1),seed=seed+i,debug_print=False,counting_operations=True);s.use_same_registers_as(c);s.write_across_shots(q,a);s.write_across_shots(keep,g);s.do(c)
                ne+=int(np.logical_or.reduce([(s.read_across_shots(q)!=want).any(0),(s.read_across_shots(keep)!=g).any(0),s.read_across_shots(scratch).any(0),s.read_phase_flipped_across_shots()]).sum());shots+=len(cases1);paid+=int(s.operation_statistics().num_toffoli_like)
        stats=dict(c.operation_statistics())
        row=dict(file=str(p),width=c.num_qubits,ops=len(c),CCX=stats.get('CCX',0),HMR=stats.get('HMR',0),static_paid=int(c.operation_statistics().num_toffoli_like),paid=paid,mean_paid=paid/shots,sha=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),cases=shots,errors=ne)
        print(row,flush=True);ans.append(row)
    Path('normalize_hmr_receipt.json').write_text(json.dumps(ans,indent=2)+'\n');assert not any(x['errors'] for x in ans)
if __name__=='__main__':main()
