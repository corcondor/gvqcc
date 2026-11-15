#!/usr/bin/env python3
"""Construct distinct GF4 mixed-place rank-42 starts for exact GF(2^12) multiplication.

Four finite rational points, infinity, and three distinct degree-two places
give 11 GF4 evaluation coordinates. This differs from the installed seven
GF8-point interpolation. No quantum circuit or existing result is modified.
"""
from pathlib import Path
from itertools import combinations, product
import hashlib
import importlib.util
import json
import sys
from theory_bilinear_prepare import gf_mul, evaluate, rank

ROOT=Path(__file__).parent
BASE=ROOT.parent

def power(a,n,degree,modulus):
    z=1
    while n:
        if n&1:z=gf_mul(z,a,degree,modulus)
        a=gf_mul(a,a,degree,modulus);n>>=1
    return z

def inverse_columns(columns):
    n=len(columns)
    rows=[sum(((c>>i)&1)<<j for j,c in enumerate(columns)) | (1<<(n+i)) for i in range(n)]
    for j in range(n):
        k=next((k for k in range(j,n) if rows[k]>>j&1),None)
        if k is None:raise ValueError('singular')
        rows[j],rows[k]=rows[k],rows[j]
        for k in range(n):
            if k!=j and rows[k]>>j&1:rows[k]^=rows[j]
    return [x>>n for x in rows]

def apply(rows,x):
    return sum(((r&x).bit_count()&1)<<i for i,r in enumerate(rows))

def linear_combination(columns,x):
    z=0
    for i,c in enumerate(columns):
        if x>>i&1:z^=c
    return z

def factor_lines(terms):
    s=set(u for u,_,_ in terms)
    return sum((a^b) in s for a,b in combinations(s,2))//3

def projective_classes(quadratic,rational):
    """PGL2(GF4) on the six Frobenius-conjugate pairs outside GF4."""
    index={x:i for i,orb in enumerate(quadratic) for x in orb}
    multiply=lambda a,b:gf_mul(a,b,4,0x13)
    permutations=set()
    for a,b,c,d in product(rational,repeat=4):
        if multiply(a,d)^multiply(b,c)==0:continue
        permutation=[]
        for orb in quadratic:
            x=orb[0];num=multiply(a,x)^b;den=multiply(c,x)^d
            assert den
            permutation.append(index[multiply(num,power(den,14,4,0x13))])
        permutations.add(tuple(permutation))
    remaining=set(combinations(range(6),3));classes=[]
    while remaining:
        seed=min(remaining)
        orbit={tuple(sorted(p[i] for i in seed)) for p in permutations}
        assert orbit<=remaining
        classes.append(sorted(orbit));remaining-=orbit
    return {'permutation_count':len(permutations),'classes':classes,'representatives':[c[0] for c in classes]}

def main():
    source=BASE/'official_sources/Syed_v12/source/dqi_source/src/controller_work/night_root/extension24_tensor.py'
    spec=importlib.util.spec_from_file_location('mixed42_small_fields',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    small9=module.small_tensor()
    small3=((1,1,3),(2,2,1),(3,3,2))
    alpha16=next(a for a in range(2,16) if gf_mul(a,a,4,0x13)^a^1==0)
    alpha12=next(a for a in range(2,4096) if gf_mul(a,a)^a^1==0)
    embed4_16=lambda x:(x&1)^((x>>1)*alpha16)
    embed4_12=lambda x:(x&1)^((x>>1)*alpha12)
    inverse4={embed4_16(x):x for x in range(4)}
    rational=sorted(inverse4)
    quadratic=[];used=set(rational)
    for a in range(16):
        if a in used:continue
        other=power(a,4,4,0x13)
        assert other!=a
        used.update([a,other]);quadratic.append((a,other))
    assert len(quadratic)==6 and len(used)==16
    for theta in range(2,4096):
        columns=[gf_mul(power(theta,i,12,0x1053),embed4_12(1<<j)) for i in range(6) for j in range(2)]
        try:tower_rows=inverse_columns(columns)
        except ValueError:continue
        break
    def poly_eval(bits,point,highest):
        if point is None:return (bits>>(2*highest))&3
        out=0
        for i in range(highest+1):
            out^=gf_mul(embed4_16((bits>>(2*i))&3),power(point,i,4,0x13),4,0x13)
        return inverse4[out] if point in inverse4 else out
    original=json.loads((ROOT/'theory_bilinear_input_certificate.json').read_text())['records'][0]['terms']
    records=[];directory=BASE/'symmetry_dqi_mixed42_runs';directory.mkdir(exist_ok=True)
    for number,chosen in enumerate(combinations(range(6),3)):
        sites=[(p,2,small3) for p in rational]+[(None,2,small3)]+[(quadratic[k][0],4,small9) for k in chosen]
        offsets=[];off=0
        for p,width,t in sites:offsets.append(off);off+=width
        assert off==22
        def encode(bits,highest):
            return sum(poly_eval(bits,p,highest)<<off for (p,w,t),off in zip(sites,offsets))
        inverse_eval=inverse_columns([encode(1<<j,10) for j in range(22)])
        def product_output(coordinates):
            polynomial=apply(inverse_eval,coordinates);out=0
            for k in range(11):
                out^=gf_mul(embed4_12((polynomial>>(2*k))&3),power(theta,k,12,0x1053))
            return out
        terms=[]
        for (point,width,small_terms),offset in zip(sites,offsets):
            evaluation_columns=[poly_eval(apply(tower_rows,1<<j),point,5) for j in range(12)]
            evaluation_rows=[sum(((v>>i)&1)<<j for j,v in enumerate(evaluation_columns)) for i in range(width)]
            output_columns=[product_output(1<<(offset+j)) for j in range(width)]
            for u,v,w in small_terms:
                terms.append((linear_combination(evaluation_rows,u),linear_combination(evaluation_rows,v),linear_combination(output_columns,w)))
        assert len(terms)==42 and all(all(t) for t in terms)
        for i in range(12):
            for j in range(12):assert evaluate(terms,1<<i,1<<j)==gf_mul(1<<i,1<<j)
        p=directory/f'input_{number:02d}.txt';p.write_text('12 42\n'+''.join(' '.join(map(str,t))+'\n' for t in terms))
        records.append({'number':number,'quadratic_orbits':chosen,'terms':terms,'input_file':str(p),'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                        'basis_pair_checks':144,'factor_lines':factor_lines(terms),'distinct_u':len({u for u,v,w in terms})})
    result={'status':'20_EXACT_MIXED_PLACE_STARTS','field_modulus':0x1053,'small4_in16':alpha16,'small4_in12':alpha12,'tower_generator':theta,
            'quadratic_orbits':quadratic,'ordinary_gf8_factor_lines':factor_lines(original),'rank':42,'binary_evaluation_dimension':22,
            'point_recipe':'4 finite GF4 points + infinity + 3 degree-two GF4 places; costs 5*3+3*9=42',
            'small9_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'records':records}
    result['PGL2_GF4_orbits']=projective_classes(quadratic,rational)
    output=ROOT/'symmetry_dqi_mixed42_20261115_inputs.json';output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'}));print('new factor line counts:',sorted({r['factor_lines'] for r in records}))

if __name__=='__main__':main()
