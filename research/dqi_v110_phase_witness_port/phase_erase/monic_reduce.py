"""Remove leading terms from raw even D,N using normalized odd D words.

Produces P_raw mod B and/or A_raw mod B (with leading terms untouched).
It is an involution; no syndrome-dependent classical operands are used.
"""
import json,hashlib
from pathlib import Path
import numpy as np
import kickmix as km
import crt882 as C
import joint_phase as J
L=json.loads(Path('raw_audit.json').read_text())['layout']

def build(selector, shared):
    b=km.CircuitBuilder()
    b.set_max_qubits(900)
    q=list(b.create_quantum_register(865,'raw'))
    def regs(words):return [[q[i] for i in w] for w in words]
    B=regs(L['D'][1:35:2])
    targets=[L[x][::2] for x in selector]
    packed=[regs(t) for t in targets]
    assert any(packed) and len(B)==17
    assert all(len(s)==18 for s in packed)
    if not shared:
        for p in packed:
            for j in range(17):J.arith(b,'prod',p[-1],B[j],p[j],12,C.MOD)
    else:
        # Transpose the raw rank-42 program across words and sectors. Only self-bank CNOT
        # instructions can be batched. All 510 instructions of the pinned tensor are checked.
        for g in C.CODES:
            a=g%64
            c=g//64%64
            if g>=4096:
                assert a<12<=c<24 and 24<=g//4096-1<36
                t=g//4096-25
                for j in range(17):
                    for p in packed:b.ccx(p[-1][a],B[j][c-12],p[j][t])
            elif a<12:
                assert c<12
                for p in packed:b.cx(p[-1][a],p[-1][c])
            elif a<24:
                assert 12<=c<24
                for j in range(17):b.cx(B[j][a-12],B[j][c-12])
            else:
                assert 24<=a<36 and 24<=c<36
                for j in range(17):
                    for p in packed:b.cx(p[j][a-24],p[j][c-24])
    return b.finish_circuit(),targets

def verify(selector,shared):
    c,targets=build(selector,shared)
    p=Path('monic_'+selector+('_shared' if shared else '_baseline')+'.kmb')
    c.to_file(str(p),format='kmb')
    c=km.Circuit.from_file(str(p))
    q=km.array([km.q(i) for i in range(865)])
    rng=np.random.default_rng(410233)
    n=err=back_err=paid=0
    for k in range(16):
        start=rng.integers(0,2,(865,64),dtype=bool)
        def read(w):return (start[w]*np.uint16(1<<np.arange(12))[None,:,None]).sum(axis=1)
        mat=read(L['D'][1:35:2])
        want=start.copy()
        for t in targets:
            coeff=read(t)
            delta=np.array([[C.m(int(x),int(y)) for x,y in zip(z,coeff[-1])] for z in mat],np.uint16)
            want[t[:17]]^=(delta[:,None,:]>>np.arange(12)[None,:,None])&1!=0
        s=km.Simulator(batch_size=64,seed=1209+k,counting_operations=True,debug_print=False)
        s.use_same_registers_as(c)
        s.write_across_shots(q,start)
        s.do(c)
        err+=int(((s.read_across_shots(q)!=want).any(0)|s.read_phase_flipped_across_shots()).sum())
        paid+=int(s.operation_statistics().num_toffoli_like)
        s.do(c)
        back_err+=int(((s.read_across_shots(q)!=start).any(0)|s.read_phase_flipped_across_shots()).sum())
        n+=64
    return dict(selector=selector,shared=shared,width=c.num_qubits,ops=len(c),stats=dict(c.operation_statistics()),
                mean_paid=paid/n,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),
                shots_each_direction=n,errors=err,reverse_errors=back_err)
if __name__=='__main__':
    rows=[verify(k,v) for k in ('N','DN') for v in (False,True)]
    assert all(x['errors']==x['reverse_errors']==0 and x['mean_paid']==714*len(x['selector']) for x in rows)
    print(json.dumps(rows,indent=2))
