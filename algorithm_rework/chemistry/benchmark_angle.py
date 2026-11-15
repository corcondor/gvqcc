#!/usr/bin/env python3
"""Compare the actual incumbent and scheduled ANGLE families in KickMix."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time

import kickmix as km
import numpy as np

def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True,type=Path)
    p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--verifiers',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--repeats',default=3,type=int)
    args=p.parse_args()
    sys.path.insert(0,str(args.verifiers))
    from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
    from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors
    models=dict(base=args.base,candidate=args.candidate)
    circuits={name:[km.Circuit.from_file(path/f'angle_k_{k}.kmb') for k in range(15)] for name,path in models.items()}
    stats={}
    for model in circuits:
        c = circuits[model]
        counts=Counter()
        for ang in c:
            counts.update(line.split()[0] for line in str(ang).splitlines()
                          if line and not line.startswith(('REGISTER ','APPEND_TO_REGISTER ')))
        assert sum(counts.values())==sum(len(ang) for ang in c)
        stats[model]={'ops':dict(counts),'count':sum(counts.values()),'max_q':max(ang.num_qubits for ang in c)}
    assert sum(stats[model]['ops']['CCX'] for model in models)==8060
    measurements={model:[] for model in models}
    fingerprints=[]
    for cycle in range(args.repeats+1):
        for model in (('base','candidate') if cycle%2==0 else ('candidate','base')):
            start=time.perf_counter()
            words,layout,t=recover_words_from_circuits(circuits[model],num_vectors=1220,
                        num_angles=75,shots_per_address=64,seed=2026111507)
            elapsed=time.perf_counter()-start
            fingerprints.append(sha256(np.asarray(words,dtype=np.uint8).tobytes()).hexdigest())
            assert t==8060
            if cycle:measurements[model].append(elapsed)
            print(cycle,model,elapsed,flush=True)
    assert len(set(fingerprints))==1 and fingerprints[0]=='8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea'
    result={'timing_scope':'native forward and reverse ANGLE, 78080 inputs, identical integer angles and CCX',
            'excluded_warmup_cycles':1,'timing_seconds':measurements,
            'timing_medians':{name:statistics.median(vals) for name,vals in measurements.items()},
            'angle_fingerprint':fingerprints[0],'stats':stats}
    args.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    main()
