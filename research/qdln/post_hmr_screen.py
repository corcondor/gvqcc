"""Native ANGLE post-HMR reachable-support scanner (Python+NumPy).

Invoke: python research/qdln/post_hmr_screen.py /path/to/public_V8.zip
Phase/Z/CZ gates are ignored ONLY for computational state evolution. This
does NOT constitute a full KickMix verifier or a new submitted circuit.
"""
from __future__ import annotations
import argparse
import io
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from native_warmstart import read_kmb
from exact_projection import rank, basis, contains


def initial(words, bank, nq):
    n = len(words)
    wires = [0]*nq
    for a in range(n):
        both = (1 << a) | (1 << (n+a))
        for j in range(11):
            if (a >> j) & 1:
                wires[j] |= both
        for word in range(5):
            if bank:
                previous = int(words[a, 5*(bank-1)+word])
                for bit in range(7):
                    if (previous >> bit) & 1:
                        wires[11+word*7+bit] |= 1 << a
            current = int(words[a, 5*bank+word])
            for bit in range(7):
                if (current >> bit) & 1:
                    wires[11+word*7+bit] |= 1 << (n+a)
    return wires


def expected(words,bank,nq):
    s=initial(words,bank,nq)
    n=len(words)
    for j in range(5):
        for bit in range(7):
            d=0
            for a in range(n):
                now=int(words[a,5*bank+j])
                prev=int(words[a,5*(bank-1)+j]) if bank else 0
                if ((now^prev)>>bit)&1:
                    d |= 1<<a
            s[11+7*j+bit] ^= d | (d<<n)
    return s


def scan_one(ops, nq, words, bank):
    s=initial(words,bank,nq)
    full=(1<<(2*len(words)))-1
    start=list(s);products=[];segments=[]
    measurements=0;dead=0;affine=0
    for op_index,(op,qs) in enumerate(ops):
        if op==0x31:
            a,b,t=qs
            v=s[a]&s[b]
            dead+=not bool(v)
            allowed=basis([full]+[x for i,x in enumerate(s) if i!=t])
            affine+=contains(allowed,v)
            products.append(v)
            s[t]^=v
        elif op==0x21:
            a,b=qs
            s[b]^=s[a]
        elif op==0x11:
            s[qs[0]]^=full
        elif op==0x50:
            r0=rank(start+[full])
            r1=rank(start+[full]+products)-r0
            r2=rank(start+[full]+s)-r0
            segments.append(dict(index=measurements,paid=len(products),
                                innovative_AND_dimension=r1,
                                nonlinear_output_dimension=r2))
            s[qs[0]]=0
            start=list(s);products=[];measurements+=1
        elif op in (0x10,0x20,0x90,0xa0):
            pass
        else:
            raise ValueError(f'Unsupported ANGLE opcode {op:#x} at {op_index}')
    r0=rank(start+[full])
    segments.append(dict(index=measurements,paid=len(products),
                         innovative_AND_dimension=rank(start+[full]+products)-r0,
                         nonlinear_output_dimension=rank(start+[full]+s)-r0))
    target=expected(words,bank,nq)
    mismatches=sum((s[j]^target[j]).bit_count() for j in range(nq))
    return dict(bank=bank,legal_states=2*len(words),paid=sum(x['paid'] for x in segments),
                HMR=measurements,dead_CCX=dead,affine_replaceable_CCX=affine,
                computational_bit_mismatches=mismatches,
                phase_verified=False,segments=segments)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('archive')
    p.add_argument('--output',default='qdln_post_hmr_screen.json')
    args=p.parse_args()
    result=[]
    with zipfile.ZipFile(args.archive) as z:
        words=np.load(io.BytesIO(z.read('dfthcsos/submission.npz')))['angle_words']
        for k in range(15):
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'kmb.kmb'
                path.write_bytes(z.read(f'dfthcsos/angle_k_{k}.kmb'))
                nq,c,ops=read_kmb(path)
            r=scan_one(ops,nq,words,k)
            assert r['paid']==c['qqq'] and r['computational_bit_mismatches']==0
            result.append(r)
            print(k,'paid',r['paid'],'dead',r['dead_CCX'],
                  'affine',r['affine_replaceable_CCX'],flush=True)
    report={'status':'COMPUTATIONAL_REACHABLE_SUPPORT_ONLY_NOT_PHASE_VERIFIED',
            'total_paid':sum(r['paid'] for r in result),
            'total_test_states':sum(r['legal_states'] for r in result),
            'batches':result}
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print('WROTE',args.output)


if __name__=='__main__':
    main()
