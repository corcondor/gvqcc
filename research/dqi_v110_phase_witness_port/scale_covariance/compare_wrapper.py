"""Compare actual serialized conjugation against a host-frame reference."""
import json, sys
from pathlib import Path
import kickmix as km
import numpy as np
import paired_mask as P
def run(a,S,M,b):
    q,m,w=map(km.array,P.V.validate_registers(a,P.SPEC))
    sx=P.V.to_bits(S,12);mx=P.V.to_bits(M,12)
    sim=km.Simulator(batch_size=len(S),seed=102362+b,counting_operations=True,debug_print=False)
    sim.use_same_registers_as(a);sim.write_across_shots(q,sx);sim.write_across_shots(m,mx);sim.do(a)
    R=(sim.read_across_shots(q).T.reshape(len(S),70,12)@(1<<np.arange(12))).astype(np.int32)
    return R,sim.read_phase_flipped_across_shots(),sim.read_across_shots(w),sim.read_across_shots(m)!=mx,sim.operation_statistics().num_toffoli_like
if __name__=='__main__':
    core,wrapped=[km.Circuit.from_file(x) for x in sys.argv[1:3]]
    power=P.EXP[np.arange(1,71)];inverse=P.EXP[-np.arange(1,71)%4095];checks=0
    # Both native circuits are run, with exactly matched measurement seeds.
    for b,(S,M,p) in enumerate(P.load_archive(Path(sys.argv[3]))):
        ret=run(core,P.vm(S,power[None,:]),np.roll(M,1,axis=1),b)
        ref=(P.vm(ret[0],inverse[None,:]),ret[1],ret[2],np.roll(ret[3].reshape(4095,12,len(S)),-1,axis=0).reshape(ret[3].shape),ret[4])
        got=run(wrapped,S,M,b)
        for u,v in zip(ref,got,strict=True):assert np.array_equal(u,v)
        checks+=len(S)
        print(b,checks,flush=True)
    Path(sys.argv[4]).write_text(json.dumps(dict(shots=checks,
        compared=['all 840 return bits','phase','ancilla','all mask bits','paid gate totals'],
        discrepancies=0),indent=2)+'\n')
