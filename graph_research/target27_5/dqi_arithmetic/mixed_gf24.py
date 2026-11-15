#!/usr/bin/env python3
"""Construct exact rank-99 GF24 tensors from GF8 quadratic evaluation sites."""
from functools import cache
from itertools import combinations, product
from pathlib import Path
import argparse
import hashlib
import json
import sys

def xor(v):
    out=0
    for x in v:out^=x
    return out

def dot(a,b):
    return (a&b).bit_count()&1

def linear(cols, x):
    return xor(c for i,c in enumerate(cols) if x>>i&1)

def apply_rows(rows,x):
    return sum(dot(r,x)<<i for i,r in enumerate(rows))

def inverse_rows(cols):
    n=len(cols)
    rows=[sum(((c>>i)&1)<<j for j,c in enumerate(cols)) | 1<<(n+i)
          for i in range(n)]
    for j in range(n):
        k=next((k for k in range(j,n) if rows[k]>>j&1),None)
        if k is None:return None
        rows[j],rows[k]=rows[k],rows[j]
        for k in range(n):
            if k!=j and rows[k]>>j&1:rows[k]^=rows[j]
    return [r>>n for r in rows]

def mul(a,b,n,modulus):
    z=0
    while b:
        if b&1:z^=a
        b>>=1
        a<<=1
        if a>>n:a^=modulus
    return z

def k24(a,b):
    f=lambda a,b:mul(a,b,12,0x1053)
    a0,a1,b0,b1=a&4095,a>>12,b&4095,b>>12
    lo,hi=f(a0,b0),f(a1,b1)
    return (lo^f(2048,hi))|((lo^f(a0^a1,b0^b1))<<12)

def power(a,n,multiplication):
    out=1
    while n:
        if n&1:out=multiplication(out,a)
        a=multiplication(a,a);n>>=1
    return out

def field_embed(n,multiplication,source_polynomial):
    for a in range(2,1<<n):
        if xor(power(a,j,multiplication) for j in range(4) if source_polynomial>>j&1)==0:
            return [linear([1,a,multiplication(a,a)],i) for i in range(8)]
    raise AssertionError("no cubic basis root")

def interpolation_sites(multiplication,rational,quadratic):
    index={x:i for i,dual in enumerate(quadratic) for x in dual}
    symmetry=set()
    for a,b,c,d in product(rational,repeat=4):
        if multiplication(a,d)==multiplication(b,c):continue
        perm=[]
        for x,_ in quadratic:
            den=multiplication(c,x)^d
            assert den
            out=multiplication(multiplication(a,x)^b,power(den,62,multiplication))
            perm.append(index[out])
        symmetry.add(tuple(perm))
    assert len(symmetry)==504
    remaining=set(combinations(range(28),3))
    records=[]
    while remaining:
        triple=min(remaining)
        orbit={tuple(sorted(pi[i] for i in triple)) for pi in symmetry}
        assert orbit <= remaining
        records.append((triple,len(orbit)))
        remaining-=orbit
    return records

def basis_pairs(terms):
    for i,j in product(range(24),repeat=2):
        value=xor(w for u,v,w in terms if (u>>i)&(v>>j)&1)
        assert value==k24(1<<i,1<<j), (i,j,value)
    return 576

def factor_lines(terms):
    factors={u for u,_,_ in terms}
    return sum(a^b in factors for a,b in combinations(factors,2))//3

def generate(repo,source,out):
    sys.path.insert(0,str(source))
    import kickmix as km
    import tower_inverse as ti
    field3, field6=km.GF2Field(3),km.GF2Field(6)
    k3, k6=ti.kernel(3),ti.kernel(6)
    assert len(k3)==6 and len(k6)==15
    assert field3.modulus in (0b1011,0b1101)
    embed64=field_embed(6,field6.mul,field3.modulus)
    embed24=field_embed(12,k24,field3.modulus)
    assert all(field6.mul(embed64[x],embed64[y])==embed64[field3.mul(x,y)] and
               k24(embed24[x],embed24[y])==embed24[field3.mul(x,y)]
               for x,y in product(range(8),repeat=2))
    collapse={v:i for i,v in enumerate(embed64)}
    seen=set(embed64)
    pairs=[]
    for a in range(64):
        if a in seen:continue
        b=field6.pow(a,8)
        assert b not in seen and b!=a
        pairs.append((a,b))
        seen.update((a,b))
    assert len(pairs)==28
    orbits=interpolation_sites(field6.mul,embed64,pairs)
    assert sum(card for _,card in orbits)==3276
    theta=1<<12
    while True:
        powers=[power(theta,i,k24) for i in range(15)]
        columns=[k24(powers[i],embed24[1<<j]) for i in range(8) for j in range(3)]
        rows=inverse_rows(columns)
        if rows is not None:break
        theta+=1
    def evaluation(poly,x,degree):
        if x is None:return (poly>>(3*degree))&7
        result=0
        for i in range(degree,-1,-1):
            result=field6.mul(result,x)^embed64[(poly>>(3*i))&7]
        return collapse[result] if x in collapse else result
    out.mkdir(exist_ok=True)
    board=json.loads((repo/'theory_bilinear_input_certificate.json').read_text())
    installed=board['records'][1]['terms']
    records=[]
    for number,(triple,orbit_size) in enumerate(orbits):
        sites=[(x,3,k3) for x in embed64]+[(None,3,k3)]+[(pairs[p][0],6,k6) for p in triple]
        off=0
        offsets=[]
        for _,width,_ in sites:offsets.append(off);off+=width
        assert off==45
        def encode(polynomial):
            return sum(evaluation(polynomial,x,14)<<off
                       for (x,_,_),off in zip(sites,offsets))
        decoding=inverse_rows([encode(1<<i) for i in range(45)])
        assert decoding is not None
        eval_cols=[k24(powers[i],embed24[1<<j]) for i in range(15) for j in range(3)]
        def collapse_product(evaluated):
            return linear(eval_cols,apply_rows(decoding,evaluated))
        terms=[]
        for (x,width,local),off in zip(sites,offsets):
            eval_in=[evaluation(apply_rows(rows,1<<i),x,7) for i in range(24)]
            scalar_forms=[sum(((z>>k)&1)<<i for i,z in enumerate(eval_in))
                          for k in range(width)]
            out_mapping=[collapse_product(1<<(off+i)) for i in range(width)]
            terms.extend((linear(scalar_forms,a),linear(scalar_forms,b),linear(out_mapping,w))
                         for a,b,w in local)
        assert len(terms)==99 and all(all(t) for t in terms)
        checks=basis_pairs(terms)
        p=out/f'start_{number:02d}.txt'
        p.write_text('24 99\n'+''.join(' '.join(map(str,t))+'\n' for t in terms))
        records.append(dict(file=p.name,sites=triple,orbit_size=orbit_size,
                            factor_lines=factor_lines(terms),basis_checks=checks,
                            sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    receipt=dict(representation='GF4096[t]/(t^2+t+2048)',
                 interpolation='P1 over GF8, 9 rational places and 3 degree2 places',
                 site_orbits=len(orbits),all_3276_site_configurations_classified=True,
                 basis_embedding_gf8_to_gf64=embed64,basis_embedding_gf8_to_gf24=embed24,
                 theta=theta,rank=99,installed_factor_lines=factor_lines(installed),records=records)
    (out/'starts.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('orbits',len(orbits),'new line counts',sorted({r['factor_lines'] for r in records}),
          'installed',receipt['installed_factor_lines'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    generate(a.repo,a.source,a.out)
