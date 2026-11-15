#!/usr/bin/env python3
"""Prepare a cross-only tensor search from the new shared J4 mixed products.

Unlike a formal quadratic COMM tensor, this intentionally quotients out
pure-low and pure-high functions, which have actual linear implementations
in the complete feature banks. The final compiler still checks the exact
1232-address residual and all quantum measurement phases.
"""
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
import numpy as np

def bits(x):
    while x:
        b=x&-x;yield b.bit_length()-1;x^=b

def rank(rows):
    p={}
    for x in rows:
        while x and x.bit_length()-1 in p:x^=p[x.bit_length()-1]
        if x:p[x.bit_length()-1]=x
    return len(p)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pool',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    row=np.load(a.pool,allow_pickle=False)[0]
    vs=[int(row[i])|(int(row[i+1])<<64) for i in range(0,len(row),2)]
    mixed=list(zip(vs[::3],vs[1::3],vs[2::3]));cross=[];lowmask=(1<<15)-1
    groups=defaultdict(lambda:[0]*15)
    for x,y,w in mixed:
        for h,l in ((x>>15,y&lowmask),(y>>15,x&lowmask)):
            if h and l and w:
                cross.append((h,l,w))
                for j in bits(l):groups[w][j]^=h
    expected=sum((rank(matrix)+1)//2 for matrix in groups.values())
    a.out.write_text(f'76 15 28 {len(cross)} {expected}\n'+''.join(f'{h&((1<<64)-1)} {h>>64} {l} {w}\n' for h,l,w in cross))
    receipt=dict(status='CROSS_ONLY_SEARCH_INPUT_PREPARED',source=str(a.pool),source_sha256=hashlib.sha256(a.pool.read_bytes()).hexdigest(),
        input=str(a.out),input_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest(),original_mixed_terms=len(mixed),
        cross_terms=len(cross),grouped_rank_cost=expected,dimensions=[76,15,28])
    a.out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
