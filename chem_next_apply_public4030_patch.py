#!/usr/bin/env python3
"""Apply the new W/H2_I patch to the exact original public4030 factorization.

The source can be its NPZ or a submission ZIP containing that NPZ. Other NPZ
arrays are preserved exactly. This command does not submit or modify circuits.
"""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np

SOURCE_SHA='4df35abdeec320a3f1c10f6f533e73550e50bb45d95e666deaa01062810a3559'
PATCH_SHA='ce9a087668d181478044fd800dc24588b21c9270d522d4fac4742f780075789d'
ARRAY_SHA={'W':'7f61a163034f30cee9ffe76bfc2cab8ddd4a0e7b798f63068781d820f9d77569',
           'H2_I':'1dd71d35408723f83597c6c6092cf13cf4d24d961d0cdf0cad3c320b92e1b15c'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--weights',type=Path,default=Path(__file__).with_name('chem_next_public4030_weights.npz'))
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.with_suffix('.receipt.json').exists():
        raise FileExistsError('Use a new output path')
    if a.source.suffix.lower()=='.zip':
        with zipfile.ZipFile(a.source) as z:blob=z.read('dfthcsos/submission.npz')
    else:blob=a.source.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=SOURCE_SHA:
        raise ValueError('The source is not the exact pinned original public4030 NPZ')
    if hashlib.sha256(a.weights.read_bytes()).hexdigest()!=PATCH_SHA:
        raise ValueError('Unexpected weight patch bytes')
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:data={k:z[k].copy() for k in z.files}
    with np.load(a.weights,allow_pickle=False) as z:replacement={k:z[k].copy() for k in z.files}
    if set(replacement)!={'W','H2_I'}:raise ValueError('Unexpected replacement key')
    before={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in data.items()}
    for k,v in replacement.items():
        if v.shape!=data[k].shape or v.dtype!=data[k].dtype:
            raise ValueError(f'{k} shape or dtype changed')
        if hashlib.sha256(v.tobytes()).hexdigest()!=ARRAY_SHA[k]:
            raise ValueError(f'{k} does not match the verified candidate')
        data[k]=v
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('xb') as f:np.savez_compressed(f,**data)
    with np.load(a.out,allow_pickle=False) as z:
        assert z.files==list(data)
        for k,v in data.items():assert np.array_equal(z[k],v),k
    retained={k:hashlib.sha256(v.tobytes()).hexdigest()==before[k] for k,v in data.items() if k not in replacement}
    assert all(retained.values())
    receipt=dict(status='PATCH_APPLIED_EXACT_ARRAYS_CHECKED',source_npz_sha256=SOURCE_SHA,
       patch_sha256=PATCH_SHA,output_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest(),
       replacement_keys=list(replacement),unchanged_arrays=retained,
       circuits_changed=False,new_full_circuit_verification_run=False,kaggle_submitted=False,
       instruction='Retain all 15 pinned public4030 loaders. Run the unchanged official verifier before final submission.')
    a.out.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
