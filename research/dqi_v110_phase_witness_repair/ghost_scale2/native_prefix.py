"""Read the selected physical KMB prefix with KickMix, preserving input order."""
import sys,struct,pathlib
import numpy as np
import kickmix as km
import verify_submission_dqi as V

prefix=km.Circuit.from_file(sys.argv[1])
q,m,a=map(km.array,V.validate_registers(prefix,V.ProblemSpecDQI.benchmark_instance()))
allq=km.array([km.q(i) for i in range(900)])
with open(sys.argv[2],'rb') as f,open(sys.argv[3],'wb') as out:
    nb,=struct.unpack('<I',f.read(4))
    for st in range(nb):
        n,=struct.unpack('<I',f.read(4))
        vals=[np.unpackbits(np.frombuffer(f.read(l*8),np.uint8).reshape(l,8),axis=1,bitorder='little')[:,:n].astype(bool) for l in (840,49140)]
        expected=np.unpackbits(np.frombuffer(f.read(8),np.uint8),bitorder="little")[:n].astype(bool)
        s=km.Simulator(batch_size=n,seed=64572+st,counting_operations=False,debug_print=False)
        s.use_same_registers_as(prefix);s.write_across_shots(q,vals[0]);s.write_across_shots(m,vals[1]);s.do(prefix)
        if len(sys.argv)==5 and sys.argv[4]=='full':
            v,p,d,mx=(s.read_across_shots(q)!=vals[0]).any(0),s.read_phase_flipped_across_shots()^expected,s.read_across_shots(a).any(0),(s.read_across_shots(m)!=vals[1]).any(0)
            masks=[sum(int(b)<<j for j,b in enumerate(z)) for z in (v,p,d,mx)]
            out.write(struct.pack('<I6Q',n,*masks,0,0))
            print(st,n,flush=True)
            continue
        z=s.read_across_shots(allq)
        assert z.shape==(900,n)
        out.write(struct.pack('<I',n))
        out.write(np.packbits(np.pad(z,((0,0),(0,64-n))),axis=1,bitorder='little').tobytes())
        print(st,n,flush=True)
