"""Paired native scale diagnostic with exact outer-frame restoration."""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np
import kickmix as km
import paired_mask as P
import returned_residual as R

PINS={
 '81081a88c27b708322f0724a09197814a18646a4a9969984ab9cf76a6e6cd7fa':257,
 '518d634ede9dcf7e78a8e91264db25d544f54bf3c86caee7ebc355f618a66499':279,
}
def test(path,raw,shifts,out):
    sha=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
    base=PINS.get(sha)
    C=km.Circuit.from_file(str(path))
    q,m,a=map(km.array,P.V.validate_registers(C,P.SPEC))
    result=[]
    for b,(S,M,phase) in enumerate(P.load_archive(raw)):
        n=len(S); arms={}
        roots=[P.recover(s) for s in S]
        phase_ref=np.array([P.PAR[M[i,r]&v].sum()%2 for i,(r,v) in enumerate(roots)],bool)
        assert np.array_equal(phase_ref,phase)
        for k in shifts:
            powers=P.EXP[(k*np.arange(1,71))%4095]
            inv=P.EXP[(-k*np.arange(1,71))%4095]
            W=P.vm(S,powers[None,:])
            E=np.roll(M,k,axis=1)
            mask=P.V.to_bits(E,12)
            sim=km.Simulator(batch_size=n,seed=102362+b,counting_operations=True,debug_print=False)
            sim.use_same_registers_as(C)
            sim.write_across_shots(q,P.V.to_bits(W,12))
            sim.write_across_shots(m,mask);sim.do(C)
            v=(sim.read_across_shots(q).T.reshape(n,70,12)@(1<<np.arange(12))).astype(np.int32)
            d=v^W
            outside=P.vm(d,inv[None,:])
            assert np.array_equal(P.vm(v,inv[None,:])^S,outside)
            ph=sim.read_phase_flipped_across_shots()^phase
            anc=sim.read_across_shots(a).any(0)
            mm=(sim.read_across_shots(m)!=mask).any(0)
            paid=sim.operation_statistics().num_toffoli_like
            cases=[]
            for i,(t,u) in enumerate(zip(d,outside,strict=True)):
                def inspect(x):
                    try:return R.inspect(x)
                    except AssertionError:return dict(degree='>35',poles=[],roots=None,unaccounted_degree=None)
                it,ou=inspect(t),inspect(u)
                transport=None
                if isinstance(it['degree'],int) and it['degree']:
                    p=P.bm(t);pp=P.bm(u);g=it['degree']
                    tr=[P.mul(c,int(P.EXP[(k*(i-g))%4095])) for i,c in enumerate(p)]
                    assert tr==pp
                    transport=True
                cases.append(dict(weight=len(roots[i][0]),inside=it,outside=ou,
                    value=int(t.any()),phase=int(ph[i]),dirty=int(anc[i]),mask=int(mm[i]),
                    recurrence_transport_checked=transport))
            arms[str(k)]=dict(paid=paid,cases=cases)
        result.append(dict(batch=b,lanes=n,arms=arms))
        print(b,[[k, sum(r['value'] for r in v['cases']),sum(r['phase'] for r in v['cases'])] for k,v in arms.items()],flush=True)
    out.write_text(json.dumps(dict(circuit_sha=sha,pin=base,qubits=C.num_qubits,ops=len(C),static_paid=C.operation_statistics().num_toffoli_like,
        exponent_shifts=shifts,batches=result),separators=(',',':'))+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for f in ('circuit','archive','out'):p.add_argument(f,type=Path)
    p.add_argument('--exponents',nargs='+',type=int,default=[0,1,2])
    a=p.parse_args();test(a.circuit,a.archive,a.exponents,a.out)
