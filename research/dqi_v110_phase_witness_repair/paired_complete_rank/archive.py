"""Native paired replay. Same positions, public masks and HMR seeds across arms."""
import hashlib, json, pathlib, struct, sys
import numpy as np
import kickmix as km
import verify_submission_dqi as V

p=pathlib.Path(sys.argv[1])
c=km.Circuit.from_file(str(p))
q,m,a=map(km.array,V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance()))
rows=[]; masks=[]; total=0; paid=0
with open(sys.argv[2],'rb') as f:
    nb,=struct.unpack('<I',f.read(4))
    for i in range(nb):
        n,=struct.unpack('<I',f.read(4))
        x,y=[np.unpackbits(np.frombuffer(f.read(l*8),np.uint8).reshape(l,8),axis=1,bitorder='little')[:,:n].astype(bool) for l in (840,49140)]
        z=np.unpackbits(np.frombuffer(f.read(8),np.uint8),bitorder='little')[:n].astype(bool)
        s=km.Simulator(batch_size=n,seed=64572+i,counting_operations=True,debug_print=False)
        s.use_same_registers_as(c); s.write_across_shots(q,x);s.write_across_shots(m,y);s.do(c)
        v=(s.read_across_shots(q)!=x).any(0)
        ph=s.read_phase_flipped_across_shots()^z
        d=s.read_across_shots(a).any(0)
        mk=(s.read_across_shots(m)!=y).any(0)
        t=int(s.operation_statistics().num_toffoli_like)
        total+=n;paid+=t
        rows.append([int(x.sum()) for x in (v,ph,d,mk,v|ph|d|mk,ph&~(v|d))])
        masks.append([hex(sum(int(b)<<j for j,b in enumerate(xs))) for xs in (v,ph,d,mk,v|ph|d|mk)])
        print(i,rows[-1],t,flush=True)
    assert not f.read(1)
print(json.dumps(dict(sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),width=c.num_qubits,ops=len(c),static_paid=c.operation_statistics().num_toffoli_like,n=total,mean_paid=paid/total,errors=np.sum(rows,axis=0).tolist(),failure_bitsets=masks)))
