import json,sys
from pathlib import Path
import numpy as np,kickmix as km
t=json.loads(Path('gate_tables.json').read_text())
def value(s,ops):
    for o,a,b,*rest in ops:
        if o=='CCX': s^=(((s>>a)&1)&((s>>b)&1))<<rest[0]
        elif o=='CX':s^=((s>>a)&1)<<b
        elif ((s>>a)^(s>>b))&1:s^=(1<<a)|(1<<b)
    return s
def bits(a,n):return ((np.asarray(a,dtype=np.int64)[None,:]>>np.arange(n)[:,None])&1).astype(bool)
def make(n,ops,name,phase=False,hmr=False):
    b=km.CircuitBuilder();b.set_max_qubits(n)
    q=list(b.create_quantum_register(n,'Q'));m=list(b.create_classical_register(1,'M'))
    if phase:b.cz(q[0],m[0]);b.cz(q[3],m[0])
    for o,*a in ops:getattr(b,o.lower())(*(q[i] for i in a))
    if hmr:b.hmr(q[10],m[0])
    c=b.finish_circuit();c.to_file(name+'.kmb',format='kmb')
    c=km.Circuit.from_file(name+'.kmb');assert c.num_qubits==n
    assert int(c.operation_statistics().num_toffoli_like)==3
    return c
def check_encoded(c):
    for start in range(0,8192,256):
        x=np.arange(start,start+256);exp=[value(int(a),t['encoded']) for a in x]
        for m in (0,1):
            s=km.Simulator(batch_size=len(x),seed=97,debug_print=False);s.use_same_registers_as(c);q=c.register_data['Q'];mm=c.register_data['M']
            s.write_across_shots(q,bits(x,13));s.write_across_shots(mm,np.full((1,len(x)),bool(m)))
            s.do(c);assert np.array_equal(s.read_across_shots(q),bits(exp,13))
            assert np.array_equal(s.read_phase_flipped_across_shots(),(m*((x^(x>>3))&1)).astype(bool))
            assert np.array_equal(s.read_across_shots(mm),np.full((1,len(x)),bool(m)))
    return 16384
def check_canonical(c,d,table,hmr=False):
    for start in range(0,16384,256):
        x=np.arange(start,start+256);exp=np.array([value(int(a),table) for a in x]);rows=[]
        for cir in (c,d):
            s=km.Simulator(batch_size=len(x),seed=start+11,debug_print=False);s.use_same_registers_as(cir);q=cir.register_data['Q'];m=cir.register_data['M']
            s.write_across_shots(q,bits(x,14));s.write_across_shots(m,np.zeros((1,len(x)),bool));s.do(cir)
            actual=s.read_across_shots(q);coin=s.read_across_shots(m);phase=s.read_phase_flipped_across_shots()
            want=exp&~(1<<10) if hmr else exp
            assert np.array_equal(actual,bits(want,14));assert np.array_equal(phase,(coin[0]&((exp>>10)&1)).astype(bool) if hmr else np.zeros(len(x),bool))
            rows.append((actual,coin,phase))
        for a,b in zip(*rows):assert np.array_equal(a,b)
    return 16384
c=make(13,t['encoded'],'encoded',phase=True)
p=make(14,t['original'],'original',hmr=True);q=make(14,t['canonical'],'canonical',hmr=True)
u=make(14,t['flat_pattern'],'flat_parent');v=make(14,t['flat_replacement'],'flat_candidate')
r=dict(encoded_shots=check_encoded(c),canonical_matched_shots=check_canonical(p,q,t['original'],True),flat_matched_shots=check_canonical(u,v,t['flat_pattern']),encoded_q=c.num_qubits,encoded_ops=len(c),original_with_hmr_ops=len(p),canonical_with_hmr_ops=len(q),flat_old_ops=len(u),flat_new_ops=len(v),errors=0)
Path('native_receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
