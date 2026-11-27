"""11 clean bits for a shared masked product bank; borrow and restore one arbitrary bit.
The missing mask coordinate has dirty offset. Cancel its contribution BEFORE
computing the mask, since all payload inputs are distinct from all targets.
"""
import kickmix as km
from fixed_transport import mul,T,P

def emit_masked(b,F,c,vs,targets,dirty,mult):
    c=list(c);vs=list(map(list,vs));targets=list(map(list,targets))
    assert len(c)==12 and len(vs)==len(targets) and all(len(v)==12 for v in vs+targets)
    controls=[F,dirty]+c+[q for v in vs for q in v];out=[q for t in targets for q in t]
    assert not set(map(str,controls))&set(map(str,out)) and len(set(map(str,out)))==len(out)
    assert str(dirty) not in set(map(str,[F]+c+[q for v in vs for q in v]))
    entry=b.num_allocated_qubits;u11=list(b.alloc_qubits(11));u=[dirty]+u11
    with b.mark('masked_products_11q'):
        for v,t in zip(vs,targets):
            for a,z in zip(v,t):b.ccx(dirty,a,z)
        b.ccx(F,c[0],dirty)
        for a,z in zip(c[1:],u11):b.init_and(F,a,z)
        for v,t in zip(vs,targets):mult(b,u,v,t)
        b.ccx(F,c[0],dirty)
        m=b.alloc_bits(11);b.hmr(u11,m);b.free(u11)
        for a,r in zip(c[1:],m):b.ccz(F,a,r)
        b.free(m)
    assert b.num_allocated_qubits==entry

def at_width(b,F,payloads,c,targets,ar):
    import dqi_int_convtest as CT
    vs=[v[-1] for v in payloads];allq=[F]+list(c)+[q for v in vs for q in v]+[q for t in targets for q in t]
    live=set(CT.TR['live']);excluded={int(str(q)[1:]) for q in allq}
    assert len(live)==b.num_allocated_qubits and excluded<=live and live-excluded
    d=km.q(min(live-excluded));print('MASKED PRODUCTS 11Q',b.num_allocated_qubits,'targets',len(targets),'dirty',d,flush=True)
    emit_masked(b,F,c,vs,targets,d,ar.mul_xor0)

def tensor_mult(b,x,y,z):
    for u,v,w in T:
        a=[q for j,q in enumerate(x) if u>>j&1];c=[q for j,q in enumerate(y) if v>>j&1];d=[q for j,q in enumerate(z) if w>>j&1]
        for q in a[1:]:b.cx(q,a[0])
        for q in c[1:]:b.cx(q,c[0])
        for q in d[1:]:b.cx(d[0],q)
        b.ccx(a[0],c[0],d[0])
        for q in reversed(d[1:]):b.cx(d[0],q)
        for q in reversed(c[1:]):b.cx(q,c[0])
        for q in reversed(a[1:]):b.cx(q,a[0])
