#!/usr/bin/env python3
"""Apply only two numerical arrays to a SHA-pinned score11-derived ANGLE family."""
import argparse
from hashlib import sha256
from pathlib import Path
from shutil import copyfile
import numpy as np

SOURCE_SHA="42be33687903988f5d09e8c2f7fefc093896d841d4648fde32186f499794d347"
VERIFIED_PATCH="020a16f4c0db58290febd2de1200bc76ec4d36713bb6f89b6a358fae1ec1389b"
ACTUAL_WORDS="8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','optimized','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    assert sha256((a.source/'submission.npz').read_bytes()).hexdigest()==SOURCE_SHA
    with np.load(a.source/'submission.npz',allow_pickle=False) as f:
        result=dict(f)
    with np.load(a.optimized,allow_pickle=False) as f:
        if 'angle_words' in f:
            assert sha256(f['angle_words'].astype(np.uint8).tobytes()).hexdigest()==ACTUAL_WORDS
        else:
            assert sha256(a.optimized.read_bytes()).hexdigest()==VERIFIED_PATCH
        for key in ('W','H2_I'):
            v=f[key]
            assert v.shape==result[key].shape and v.dtype==result[key].dtype
            assert np.all(np.isfinite(v))
            result[key]=v
    a.output.mkdir(parents=True,exist_ok=False)
    for k in range(15):
        name=f'angle_k_{k}.kmb'
        copyfile(a.source/name,a.output/name)
    np.savez_compressed(a.output/'submission.npz',**result)
    print(sha256((a.output/'submission.npz').read_bytes()).hexdigest())

if __name__=='__main__':
    main()
