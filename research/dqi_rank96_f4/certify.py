"""Exact GF4-to-binary adapter for #323 full-tape rank admission.

No candidate may be admitted without all 576 original basis products,
including same-input-basis transformations. This script compiles 72Q
arbitrary-dirty-target native witnesses; it does not claim a full KMB splice.
"""
import argparse,base64,hashlib,json,random,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def par(x):return x.bit_count()&1
def mul4(a,b):
    t=0
    while b:
        if b&1:t^=a
        b>>=1;a<<=1
        if a&4:a^=7
    return t
def scale(w,k):
    return sum(mul4(w>>(2*i)&3,k)<<(2*i) for i in range(12))
def dot(a,b):
    z=0
    for i in range(12):z^=mul4(a>>(2*i)&3,b>>(2*i)&3)
    return z
def bits(x):
    while x:
        y=x&-x;yield y.bit_length()-1;x^=y
def transform(cols,x):
    r=0
    for i in bits(x):r^=cols[i]
    return r
def eval_terms(terms,x,y):
    r=0
    for a,b,c in terms:
        if par(a&x) and par(b&y):r^=c
    return r
def eval4(terms,x,y):
    r=0
    for a,b,c in terms:r^=scale(c,mul4(dot(a,x),dot(b,y)))
    return r
def originals():
    raw=zlib.decompress(base64.b64decode((ROOT/'terms.b64').read_text()))
    assert len(raw)==3564
    n=[int.from_bytes(raw[i:i+3],'little') for i in range(0,len(raw),3)]
    return [[tuple(n[j:j+3]) for j in range(i,i+297,3)] for i in (0,594)]
def expand(terms,seed):
    result=[]
    for u,v,w in terms:
        a=[sum(((dot(t,x)>>k)&1)<<i for i,x in enumerate(seed['inCols'])) for t in (u,v) for k in (0,1)]
        x,y,z,h=a
        # (a+bω)(c+dω)=(ac+bd)+(ac+(a+b)(c+d))ω.
        for l,r,c in ((x,z,3),(y,h,1),(x^y,z^h,2)):
            result.append((l,r,transform(seed['outCols'],scale(w,c))))
    assert all(0<a<1<<24 and 0<b<1<<24 and 0<c<1<<24 for a,b,c in result)
    return result
def check():
    orig=originals();seeds=json.loads((ROOT/'f4_seeds.json').read_text())
    alt=json.loads((ROOT/'f16_tower_seeds.json').read_text())
    jobs=[('crt',seeds,seeds),('tower',alt,seeds)]
    for name,fn in [('flip','f4_search_results.json'),('triple','f4_triple_results.json'),('tower_search','tower_search_results.json')]:
        jobs.append((name,json.loads((ROOT/fn).read_text()),seeds))
    allrows=[];best={}
    for name,rows,meta in jobs:
        for typ,(row,seed) in enumerate(zip(rows,meta,strict=True)):
            ts=row['terms'];assert all(0<a<1<<24 and 0<b<1<<24 and 0<c<1<<24 for a,b,c in ts)
            for i in range(12):
                for j in range(12):
                    x,y=1<<(2*i),1<<(2*j)
                    assert eval4(ts,x,y)==eval4(seed['terms'],x,y),(name,typ,i,j)
            new=expand(ts,seed)
            for i in range(24):
                for j in range(24):assert eval_terms(new,1<<i,1<<j)==eval_terms(orig[typ],1<<i,1<<j),(name,typ,i,j)
            result=dict(source=name,type=typ,GF4_products=len(ts),binary_CCX=len(new),basis_GF4=144,basis_GF2=576,eligible97=len(new)<=97)
            print(json.dumps(result),flush=True)
            allrows.append((result,new,orig[typ]))
            if typ not in best or len(new)<len(best[typ]):best[typ]=new
    return allrows,best
def native(rows,out):
    import kickmix as km,numpy as np
    rng=random.Random(2026112896);out.mkdir(parents=True,exist_ok=True);rr=[]
    for result,ts,orig in rows:
        cb=km.CircuitBuilder();cb.set_max_qubits(72);q=list(cb.create_quantum_register(72,'W'))
        for a,b,c in ts:
            A=list(bits(a));B=[24+j for j in bits(b)];Z=[48+j for j in bits(c)]
            for bank in (A,B):
                for j in bank[1:]:cb.cx(q[j],q[bank[0]])
            for j in Z[1:]:cb.cx(q[Z[0]],q[j])
            cb.ccx(q[A[0]],q[B[0]],q[Z[0]])
            for j in reversed(Z[1:]):cb.cx(q[Z[0]],q[j])
            for bank in (B,A):
                for j in reversed(bank[1:]):cb.cx(q[j],q[bank[0]])
        c=cb.finish_circuit();path=out/(result['source']+'_'+str(result['type'])+'.kmb')
        c.to_file(str(path),format='kmb');c=km.Circuit.from_file(str(path))
        assert c.num_qubits==72 and int(c.operation_statistics().num_toffoli_like)==len(ts)
        ins=[(1<<i,1<<j,rng.randrange(1<<24)) for i in range(24) for j in range(24)]
        ins.extend(tuple(rng.randrange(1<<24) for _ in range(3)) for _ in range(1024))
        expected=[(x,y,z^eval_terms(orig,x,y)) for x,y,z in ins]
        def array(a):return np.array([[(x>>j)&1 for x in w for j in range(24)] for w in a],dtype=bool).T.copy()
        A,B=array(ins),array(expected);q=km.array([km.q(j) for j in range(72)])
        for seed in (11,97):
            for st in range(0,len(ins),128):
                en=min(st+128,len(ins));s=km.Simulator(batch_size=en-st,seed=seed+st,debug_print=False,counting_operations=True);s.use_same_registers_as(c)
                s.write_across_shots(q,A[:,st:en]);s.do(c)
                assert np.array_equal(s.read_across_shots(q),B[:,st:en]) and not np.any(s.read_phase_flipped_across_shots())
                s.do(c)
                assert np.array_equal(s.read_across_shots(q),A[:,st:en]) and not np.any(s.read_phase_flipped_across_shots())
        v=dict(**result,Q=72,ops=len(c),forward=2*len(ins),inverse=2*len(ins),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rr.append(v);print('NATIVE',json.dumps(v),flush=True)
    (out/'receipt.json').write_text(json.dumps(rr,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path);p.add_argument('--admit',type=Path);a=p.parse_args()
    rows,best=check()
    if a.native:native(rows,a.native)
    if a.admit:
        # Both algebra types required for #323 all-333 strict mode.
        if any(len(best[t])>97 for t in (0,1)):
            raise SystemExit('REJECT: no <=97 certificate for both algebras; no full candidate emitted.')
        a.admit.write_text(json.dumps(dict(field=best[0],dual=best[1],expected_static_saving=329*(99-len(best[0]))+4*(99-len(best[1]))),indent=2))
