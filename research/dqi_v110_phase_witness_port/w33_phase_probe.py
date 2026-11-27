"""Independent matched-mask probes for the value-restoration witness."""
import json,os,sys
from pathlib import Path
import kickmix as km, numpy as np
sys.path.insert(0,os.environ['DQI_VERIFIER_DIR'])
import verify_submission_dqi as V
f=json.loads(Path(sys.argv[1]).read_text())
c=km.Circuit.from_file(sys.argv[2])
q,b,a=V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance())
q,b=km.array(q),km.array(b)
mags=dict(zip(f['error_indices'],f['error_values']))
pos=list(mags)+[j for j in [0,1,2,3,4,5,128,255,1024,2048,3000,4094] if j not in mags]
n=len(pos)*12
M=np.zeros((n,4095),np.int64)
for i,z in enumerate(pos): M[i*12:(i+1)*12,z]=1<<np.arange(12)
expected=V.to_bits(np.array([mags.get(z,0) for z in pos])[None,:],12).ravel()
assert expected.size==n
A=V.to_bits(np.repeat(np.asarray(f['native_rows'][0]['input'])[None,:],n,axis=0),12)
B=V.to_bits(M,12)
def run(B,seed):
    sim=km.Simulator(batch_size=n,seed=seed);sim.use_same_registers_as(c)
    sim.write_across_shots(q,A);sim.write_across_shots(b,B);sim.do(c)
    return sim.read_across_shots(q),np.asarray(sim.read_phase_flipped_across_shots())
def scalar(v):return int(np.count_nonzero(v))
summary=[]
for seed in [3011,3012,3013]:
    y0,p0=run(np.zeros_like(B),seed);y1,p1=run(B,seed)
    actual=(p0^p1)
    # Independently form the expected mask bit without relying on to_bits packing.
    exp=np.array([bool((mags.get(z,0)>>j)&1) for z in pos for j in range(12)])
    assert np.array_equal(expected,exp)
    summary.append(dict(seed=seed,shots=n,output_delta=scalar((y0!=y1).any(0)),
        bad_restore=scalar((y0!=A).any(0)),zero_mask_phase=scalar(p0),
        wrong_phase_character=scalar(actual!=exp),
        wrong_true_support=scalar((actual!=exp)[:len(mags)*12]),
        wrong_off_support=scalar((actual!=exp)[len(mags)*12:]),
        all_bad_samples=np.where(actual!=exp)[0].tolist()))
    print(json.dumps(summary[-1]),flush=True)
