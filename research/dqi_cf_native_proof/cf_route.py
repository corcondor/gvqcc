"""Source adapter for upstream dqi_int_pdrfix.py, revision a9effc... .
The new CF law is taken from the upstream docstring: B=C2=0,C=F=1.
Do not apply to the owner's private repaired source without a structural review.
All HMR helpers are the original P helpers; no new measurement convention.
"""
import ast,pathlib,argparse,hashlib

def _route_rest(b, ar, U, c, X, Bq, Cq, Fq, C2q):
    """Fused CF repair; ZCF reuses the freed ZB word, and CF flag reuses sL."""
    l1 = [(Bq, True), (Cq, False)]
    h1 = P.flag_and(b, l1)
    ZB = P.masked_word(b, h1, c[U - 2]['f'][-2])
    lo = [(Cq, True), (Fq, True)]
    o = P.flag_and(b, lo)
    l2 = [(Bq, True), (o, False)]
    h2 = P.flag_and(b, l2)
    b.cx(h2, ZB[0])
    lL = [(Bq, True), (C2q, True), (o, True)]
    sL = P.flag_and(b, lL)
    b.cx(Cq, Fq)
    lU2 = [(Bq, True), (Fq, False), (C2q, False)]
    sU2 = P.flag_and(b, lU2)
    b.cx(Cq, Fq)
    tu, tl, t2 = P.tops(U - 2), P.tops(U - 3), P.tops(U - 4)
    assert len(tu) == len(tl) == len(t2) == len(X)
    for x,s in zip(X,tu):
        ar.mul_xor0(b, ZB, s, x)
    b.cx(h2, ZB[0])
    P.erase_flag_and(b, h2, l2)
    P.erase_masked_word(b, h1, c[U - 2]['f'][-2], ZB)
    P.erase_flag_and(b, h1, l1)
    # hCF = sL AND NOT(C XOR F). On CF, sL=1 and sU2=0.
    b.cx(Cq, Fq)
    lCF = [(sL, False), (Fq, True)]
    hCF = P.flag_and(b, lCF)
    b.cx(Cq, Fq)
    qF = c[U - 3]['f'][-2]
    # Fail closed on unexpected physical aliasing. Debug words are distinct too.
    assert len(qF) == 12
    assert not set(map(str,qF)).intersection(str(q) for w in [*X,*tl,*t2] for q in w)
    ZCF = P.masked_word(b, hCF, qF)
    b.cx(sL, ZCF[0]); b.cx(hCF, ZCF[0])
    b.cx(hCF, sU2)
    for x,s,t in zip(X,tl,t2):
        ar.mul_xor0(b, ZCF, s, x)
        for j in range(12): b.ccx(sU2, t[j], x[j])
    b.cx(hCF, sU2)
    b.cx(hCF, ZCF[0]); b.cx(sL, ZCF[0])
    P.erase_masked_word(b, hCF, qF, ZCF)
    b.cx(Cq, Fq)
    P.erase_flag_and(b, hCF, lCF)
    P.erase_flag_and(b, sU2, lU2)
    b.cx(Cq, Fq)
    P.erase_flag_and(b, sL, lL)
    P.erase_flag_and(b, o, lo)

# Upstream exact blob fingerprint from PR187. Do not overwrite source.
UPSTREAM_BLOB='08224a897eb7aaa99a1f28b1b61d439cd4d4dc30'
def gitsha(s):return hashlib.sha1(f'blob {len(s)}\0'.encode()+s).hexdigest()
def adapt(src,dst):
    src,dst=pathlib.Path(src),pathlib.Path(dst)
    if dst.exists() or src.resolve()==dst.resolve():raise ValueError('refuse overwrite')
    data=src.read_bytes()
    if gitsha(data)!=UPSTREAM_BLOB:raise ValueError('unexpected upstream source; manual audit required')
    a=ast.parse(data);fn=[x for x in a.body if isinstance(x,ast.FunctionDef) and x.name=='_route_rest'];assert len(fn)==1
    fn=fn[0];me=ast.parse(pathlib.Path(__file__).read_text());mine=next(x for x in me.body if isinstance(x,ast.FunctionDef) and x.name=='_route_rest')
    lines=data.decode().splitlines(keepends=True);s=ast.get_source_segment(pathlib.Path(__file__).read_text(),mine)+'\n'
    lines[fn.lineno-1:fn.end_lineno]=[s];out=''.join(lines);b=ast.parse(out)
    def rest(x):return [ast.dump(n,include_attributes=False) for n in x.body if not(isinstance(n,ast.FunctionDef) and n.name=='_route_rest')]
    assert rest(a)==rest(b);compile(out,str(dst),'exec');dst.write_text(out)
    print('pinned upstream splice + Python compile PASS',hashlib.sha256(out.encode()).hexdigest())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('src');p.add_argument('dst');a=p.parse_args();adapt(a.src,a.dst)
