#!/usr/bin/env python3
"""Extract rank matrices and output directions from the actual incumbent."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys

import kickmix as km
import numpy as np

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('repo','loaders','words','out'):
        p.add_argument('--'+k,type=Path,required=True)
    args=p.parse_args()
    sys.path.insert(0,str(args.repo))
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'score10_followup'/'chemistry'))
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA_INDEX,extract
    from chemistry_relation_screen import advance,evaluate_form
    from chemistry_reachable_exact_proof import pack
    from score11_j5_product_circuits import highlow_matrix,rank

    words=np.load(args.words,allow_pickle=False).astype(np.uint64)
    assert words.shape in {(1220,75),(1232,75)}
    n=1216
    one=(1<<n)-1
    addresses=np.arange(n,dtype=np.uint64)
    metadata=[]
    with (args.out/'segments.bin').open('wb') as out:
        for k in range(15):
            path=args.loaders/f'angle_k_{k}.kmb'
            circuit=km.Circuit.from_file(path)
            lines=str(circuit).splitlines()
            gates=[parse_line(line) for line in lines]
            values=[0]*circuit.num_qubits
            values[:11]=[pack((addresses>>q)&1) for q in range(11)]
            if k:
                for j in range(5):
                    for b in range(8):
                        values[11+8*j+b]=pack((words[:n,5*(k-1)+j]>>b)&1)
            entry=[]
            for gate,qs,cond in gates:
                entry.append(tuple(values))
                advance(values,gate,qs,one)
            data_ccx=[i for i,(g,q,_) in enumerate(gates) if g=='CCX' and q[-1] in DATA_INDEX]
            first,last=data_ccx[0],data_ccx[-1]+1
            cuts=[i for i in range(first,last) if (
                (g:=gates[i][0]) not in ('X','CX','CCX') or gates[i][2] is not None
                or g=='CCX' and (q:=gates[i][1])[-1] not in DATA_INDEX
                or g=='CX' and (q:=gates[i][1])[0] in DATA_INDEX and q[1] not in DATA_INDEX)]
            for start,end in zip([first]+[i+1 for i in cuts],cuts+[last]):
                if not any(start<=i<end for i in data_ccx):
                    continue
                ex=extract(km.Circuit('\n'.join(lines[start:end])+'\n'))
                state=entry[start+ex['first']]
                mats=[]
                for u,v,_ in ex['terms']:
                    a,b=(evaluate_form(m,state,one) for m in (u,v))
                    assert rank(highlow_matrix(a,76)) == rank(highlow_matrix(b,76)) == 0
                    mat=highlow_matrix(a&b,76)
                    assert rank(mat)<=2
                    mats.append(mat)
                out.write(struct.pack('<I',len(mats)))
                for mat in mats:
                    out.write(struct.pack('<76H',*mat))
                metadata.append(dict(batch=k,start=start,end=end,
                    directions=[w for _,_,w in ex['terms']],source_sha256=sha256(path.read_bytes()).hexdigest()))
    (args.out/'segments.json').write_text(json.dumps(metadata,indent=2)+'\n')

if __name__=='__main__':
    main()
