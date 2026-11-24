"""V4 conditional carry bridge. Reproduce against the V3 bundle:
copy this file into central/global_chart and run python context_bridge_v4.py.
Requires the V3 modules and exact rows; the source is SHA-pinned.
Afterwards use verify_portfolio.py v4context_300 for full serialized BDD check.
No sample-only admission, no Kaggle submission.
"""
from ripple_phase_transfer import *
from itertools import combinations
from quadratic_loan import poly_factor, synth_xor
from rank1_delta import phaseonly

PIN = '6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03'

def quadratic(s, target, act, excluded):
    qs = [q for q in range(37) if q not in excluded]
    terms = [()] + [(q,) for q in qs] + list(combinations(qs,2))
    basis = {}
    r = target & act
    w = 0
    for j, term in enumerate(terms):
        v = act
        for q in term:
            v &= s[q]
        u,m = reduce(basis,v)
        if u:
            basis[u.bit_length()-1] = (u,m^(1<<j))
        r,m = reduce(basis,r)
        w ^= m
        if not r:
            return [term for k,term in enumerate(terms) if w>>k&1]
    return None

def discover_context(n=8192):
    assert hashlib.sha256(SRC.read_bytes()).hexdigest() == PIN
    rows = pickle.loads((P/'exact_rows.pkl').read_bytes())
    ats = {i:h for i in range(N) if (h:=stage(i)) is not None}
    ledger = json.loads((P/'global_phase_anf.json').read_text())
    ban = set(ledger['phase_dependent_hmr_ops']+ledger['rotation_dependent_hmr_ops'])
    phase = phaseonly()
    screen = {}
    def cb(i,o,s,c,stack,a,act,one):
        if i not in ats or stack:
            return
        _,u,v,w,d = ats[i]
        r = quadratic(s,s[v],s[v]^s[w],(v,w,d))
        if r is not None:
            screen[i] = r
    trace_cuts(n,11821,cb)
    b = BDD(NLEGAL)
    src = Machine(b,[b.leaf(mask(i,NLEGAL)) for i in range(22)]+[b.zero]*15)
    good = {}
    for i,o in enumerate(OPS):
        if i in screen:
            _,u,v,w,d = ats[i]
            p = b.xor(src.s[v],src.s[w])
            h = b.zero
            for term in screen[i]:
                f = b.one
                for q in term:
                    f = b.and_(f,src.s[q])
                h = b.xor(h,f)
            if (b.and_(p,b.xor(h,src.s[v])) is b.zero
                    and 1<<d in rows[i] and 1<<w in rows[i+7]
                    and i+6 not in ban and i+6 in phase):
                good[i] = screen[i]
        src.step(o,b.variable() if o.raw&127==80 else None)
        src.p=b.zero
        src.rot=[]
        b.clear()
    return good

def make(i,terms):
    _,a,b,c,d = stage(i)
    terms = [tuple(t) for t in terms]
    assert all(not(set(t)&{a,b,c,d}) for t in terms)
    u,v,w = map(lambda x:slot(x,d),(a,b,c))
    pre = synth_xor(terms,u,d)
    g = ([Op(33,(v,w))] + pre + [Op(49,(w,u,v))] + pre[::-1]
         + [Op(33,(u,w)),Op(34,(v,w)),Op(64,(),measurement=OPS[i+6].measurement)])
    return ('rank1',i,i+7,d,c,1<<d,1<<c,g,{'architecture':'conditional carry context',
        'removed_hmr':i+6,'context':terms,'context_quadratic_rank':len(poly_factor(terms)[0]),
        'paid_delta':stats(g)['paid']-stats(OPS[i:i+7])['paid']})

def splice(good,mode='300'):
    edges={i:make(i,t) for i,t in good.items()}
    raw=pickle.loads((P/f'portfolio_{mode}_path_unmapped.pkl').read_bytes())
    ends={e[1]:k for k,e in enumerate(raw)}
    ends[N]=len(raw)
    out=[]
    selected=[]
    k=0
    while k<len(raw):
        e=raw[k];i=e[1];new=edges.get(i)
        if new is not None and i+7 in ends:
            z=ends[i+7];old=raw[k:z]
            a=sum(stats(x[7])['paid'] for x in old)
            b=stats(new[7])['paid']
            oldcov=sum(x[2]-x[1] for x in old if x[0]!='fallback')
            if b<a or (b==a and oldcov<7):
                selected.append(dict(start=i,old_paid=a,new_paid=b,new_coverage=7-oldcov))
                out.append(new);k=z;continue
        out.append(e);k+=1
    (P/f'portfolio_v4context_{mode}_path_unmapped.pkl').write_bytes(pickle.dumps(out))
    receipt={'source_sha256':PIN,'exact_contexts':good,'selected':selected,
             'covered':sum(e[2]-e[1] for e in out if e[0]!='fallback'),
             'paid':sum(stats(e[7])['paid'] for e in out)}
    (P/f'context_bridge_v4_{mode}_plan.json').write_text(json.dumps(receipt,indent=2))
    print(receipt,flush=True)

if __name__=='__main__':
    splice(discover_context())
