"""Export all already-screened ANGLE circuits as KMX and re-check recorded gate counts.

This is separate from the append-only search ledger. No native verification.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from multi_angle_synthesis import ALGORITHMS, synthesize


def export(inputs: list[Path], ledger: Path, output: Path):
    output.mkdir(parents=True,exist_ok=True)
    by_key={(x['source'],x['method'],x['slot']):x
            for x in map(json.loads,ledger.read_text().splitlines())}
    manifest=[]
    for path in inputs:
        with np.load(path,allow_pickle=False) as d:
            words=np.asarray(d['angle_words'],np.int64)
        directory=output/path.stem
        directory.mkdir(exist_ok=True)
        for method in ALGORITHMS:
            sub=directory/method
            sub.mkdir(exist_ok=True)
            for slot in range(15):
                reference=by_key[(path.name,method,slot)]
                c,stats=synthesize(words,slot,method)
                assert stats['CCX']==reference['CCX']
                assert stats['CX']==reference['CX']
                assert stats['qubits']==reference['qubits']
                dst=sub/f'angle_k_{slot}.kmx'
                dst.write_text('\n'.join(c.kmx_lines())+'\n',encoding='utf-8')
                sha=hashlib.sha256(dst.read_bytes()).hexdigest()
                if 'sample_kmx_sha256' in reference:
                    assert sha == reference['sample_kmx_sha256'],dst
                manifest.append(dict(source=path.name,method=method,slot=slot,
                                     sha256=sha,bytes=dst.stat().st_size,
                                     path=str(dst.relative_to(output)),CCX=stats['CCX'],
                                     CX=stats['CX'],Q=stats['qubits']))
        print('EXPORTED',path.name,len(manifest),flush=True)
    (output/'all_kmx_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seeds',type=Path,nargs='+',required=True)
    ap.add_argument('--ledger',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    export(args.seeds,args.ledger,args.out)
