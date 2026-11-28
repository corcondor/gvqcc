"""Native pairing of dirty arbitrary coefficient words, outside the legal fixture subset."""
import argparse,json
from pathlib import Path
import kickmix as k,numpy as np
p=argparse.ArgumentParser();p.add_argument("original");p.add_argument("rewrite");a=p.parse_args()
c=[k.Circuit.from_file(x) for x in (a.original,a.rewrite)]
rng=np.random.default_rng(73126);q=k.array([k.q(i)for i in range(840)]);cases=0
for i in range(32):
    x=rng.integers(0,2,(840,64),dtype=bool);o=[]
    for c0 in c:
        s=k.Simulator(batch_size=64,seed=i,debug_print=False);s.use_same_registers_as(c0);s.write_across_shots(q,x);s.do(c0)
        assert not s.read_phase_flipped_across_shots().any();o.append(s.read_across_shots(q))
    assert np.array_equal(*o);cases+=64
Path("dirty_pair_receipt.json").write_text(json.dumps(dict(arbitrary_D_H_cases=cases,word_differences=0,phase_errors=0),indent=2)+'\n')
print('All paired arbitrary D,H:',cases)
