#!/usr/bin/env python3
"""Restore the verified chemistry endpoint from the pinned public v27 NPZ."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np

SOURCE_SHA='4df35abdeec320a3f1c10f6f533e73550e50bb45d95e666deaa01062810a3559'
PATCH_SHA='056b9c04f4260bbb7d099650e93916c7e5e6b876b18d16827f0c3d1060262188'
H2_SHA='0ce85c16084e3c8284d357527d03b1b4475b52f9d6b5d36ccecc0d2b7fccb704'
VERIFIED_SHA='da30619d4a668d663adc9f7f0462cfd52ba8684cc5523980f5119dc3ef90302e'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--patch',type=Path,default=Path(__file__).with_name('score8_chem_v27_identity_patch.npz'))
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    if digest(a.source)!=SOURCE_SHA:raise ValueError('Source is not the pinned public v27 NPZ')
    if digest(a.patch)!=PATCH_SHA:raise ValueError('Identity patch checksum mismatch')
    original=dict(np.load(a.source,allow_pickle=False));data=dict(original)
    h2=np.load(a.patch,allow_pickle=False)['H2_I']
    if h2.shape!=(8,44) or h2.dtype!=np.float64:raise ValueError('Unexpected identity patch layout')
    if hashlib.sha256(h2.tobytes()).hexdigest()!=H2_SHA:raise ValueError('Identity array checksum mismatch')
    data['H2_I']=h2
    assert all(np.array_equal(data[k],original[k]) for k in original if k!='H2_I')
    a.out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.out,**data)
    print(json.dumps(dict(output=str(a.out),sha256=digest(a.out),verified_sha256=VERIFIED_SHA,
        byte_identical_to_verified=digest(a.out)==VERIFIED_SHA,only_changed_array='H2_I',numpy_version=np.__version__,
        required_loader_family='All 15 exact public v27 4030-Toffoli loaders from outcome_v27_public_pins.json',
        note='The declared word table is preserved; official verification recovers actual words from the circuits.')))

if __name__=='__main__':main()
