#!/usr/bin/env python3
"""Classify C-only cache pairs under exact inverse-phase automorphisms."""
from itertools import combinations
from pathlib import Path
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
import kickmix as km

def trace(field,x):
    acc=0
    for _ in range(4):
        acc^=x
        x=field.mul(x,x)
    assert acc in (0,1)
    return acc

def dot(a,b):
    return (a&b).bit_count()&1

def plan(field):
    planes=sorted({tuple(sorted((a,b,a^b))) for a,b in combinations(range(1,16),2)})
    assert len(planes)==35
    transform=[]
    for scalar in range(1,16):
        for power in (1,2,4,8):
            cols=[field.mul(scalar,field.pow(1<<i,power)) for i in range(4)]
            covectors=[sum(dot(a,c)<<i for i,c in enumerate(cols)) for a in range(16)]
            transform.append(tuple(covectors))
    assert len(set(transform))==60
    pool=set(combinations(planes,2))
    out=[]
    while pool:
        s=min(pool)
        orbit={tuple(sorted(tuple(sorted(U[a] for a in plane)) for plane in s)) for U in transform}
        assert orbit<=pool
        out.append((s,len(orbit),len(set(s[0])&set(s[1]))))
        pool-=orbit
    assert sum(size for _,size,_ in out)==595
    return out

def run(arg):
    n, ((p,q),count,intersection), bare, out, exe=arg
    input_file=out/f'leaf_{n:02d}.txt'
    input_file.write_text(' '.join(map(str,(*p[:2],*q[:2])))+'\n'+bare+'\n')
    ret=out/f'leaf_{n:02d}.json'
    subprocess.run([str(exe),str(input_file),str(ret)],check=True,capture_output=True,text=True)
    result=json.loads(ret.read_text())
    print(n,count,intersection,result['rref_planes'],result['witness'],flush=True)
    return dict(index=n,planes=[p,q],orbit_size=count,nonzero_intersection=intersection,search=result)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('binary',type=Path)
    p.add_argument('out',type=Path)
    p.add_argument('--workers',type=int,default=1)
    a=p.parse_args()
    f=km.GF2Field(4)
    y=[]
    for x in range(256):
        b,c=x>>4,x&15
        y.append(-1 if c==0 and b else trace(f,f.mul(b,f.invert(c))) if c else 0)
    bare=' '.join(map(str,y))
    work=plan(f)
    print('orbits',len(work),'sizes',[card for _,card,_ in work],flush=True)
    a.out.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        jobs=((n,item,bare,a.out,a.binary.resolve()) for n,item in enumerate(work))
        result=list(pool.map(run,jobs))
    (a.out/'receipt.json').write_text(json.dumps(dict(orbit_results=result,orbits=len(work),
        tested_points=241,all_cache_choices_covered=595),indent=2)+'\n')
