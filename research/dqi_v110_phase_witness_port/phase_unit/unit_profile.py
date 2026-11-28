"""Word oracle and cost screen on the #261 native raw-prefix archive.

Run with #261's crt882 on PYTHONPATH and audit_raw_prefix.py's raw_words.jsonl.
Cost screen charges GF(4096) products at 42 CCX; it is not a gate count or lower bound.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

import crt882 as C


def padded(p, n):
    assert len(p) <= n
    return p + [0] * (n - len(p))


def scale(p, a):
    return C.trim([C.m(x, a) for x in p])


def merge_frame(b, a, n):
    # At infinity B/A = x**(n-m) (c[0] + c[1]/x + ...).
    m = len(a) - 1
    ai = C.inv(a[-1])
    c = [0] * n
    for j in range(n):
        x = b[n-j]
        for k in range(1, min(j, m)+1):
            x ^= C.m(a[m-k], c[j-k])
        c[j] = C.m(ai, x)
    assert c[0]
    return c


def merge(c, words, d, inverse=False):
    out = words.copy()
    n = len(words)
    if not inverse:
        for k in range(d, n):
            x = out[k]
            for j in range(1, k+1):
                out[k-j] ^= C.m(c[j], x)
            out[k] = C.m(c[0], x)
    else:
        ai = C.inv(c[0])
        for k in range(n-1, d-1, -1):
            x = out[k] = C.m(ai, out[k])
            for j in range(1, k+1):
                out[k-j] ^= C.m(c[j], x)
    return out


def action(b, a, p, inverse=False):
    """A**(-1) times P mod B, or inverse action; fixed n-word target."""
    n, m = len(b)-1, len(a)-1
    assert 0 <= m < n and len(p) == n
    if m == 0:
        k = a[0] if inverse else C.inv(a[0])
        return padded(scale(p, k), n)
    d = n-m
    _, r = C.div(b, a)
    c = merge_frame(b, a, n)
    if not inverse:
        q, s = C.div(C.trim(p.copy()), a)
        z = action(a, r, padded(s, m))
        return merge(c, padded(q, d) + z, d)
    packed = merge(c, p, d, inverse=True)
    s = action(a, r, packed[d:], inverse=True)
    return padded(C.add(C.mul(a, packed[:d]), s), n)


def from_raw(d, v):
    def root(word):
        return C.exp[(2048 * C.log[word]) % 4095] if word else 0
    a,b,p,q = [C.trim(list(map(root, w))) for w in (d[::2],d[1::2],v[::2],v[1::2])]
    _, ar = C.div(a, b)
    return b, ar, (C.div(p,b)[1], C.div(q,b)[1])


def profile(b, a):
    out = [len(b)-1]
    while a:
        out.append(len(a)-1)
        b, a = a, C.div(b, a)[1]
    assert out[-1] == 0
    return tuple(out)


def rectangular(r, s):
    # Transpose evaluation at r+s-1 distinct GF(4096) points.
    # This prices bilinear rank only, not the work to hold those evaluations.
    return min(r*s, r+s-1)


def triangular_shears(m):
    if m < 2:
        return 0
    a, b = m//2, m-m//2
    return triangular_shears(a) + triangular_shears(b) + rectangular(a,b)


def cost(path):
    school = blocked = 0
    for n,m in zip(path,path[1:]):
        if not m:
            school += n
            blocked += n
            continue
        d = n-m
        # Split P = A*p + s: m*d lower updates, d scalings.
        # Merge: m scalings and a d-by-m block followed by an m-by-m triangle.
        school += m*d+d+m + m*d+m*(m-1)//2
        # Replace cross blocks of merge only (do not assume free split).
        blocked += m*d+d+m + rectangular(d,m)+triangular_shears(m)
    return dict(school_slots=school, merge_blocked_slots=blocked,
                school_paired_ccx_model=4*42*school, merge_blocked_paired_ccx_model=4*42*blocked)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('raw',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    panels=collections.defaultdict(collections.Counter)
    checks=0
    digest=hashlib.sha256()
    with args.raw.open('rb') as f:
        for line in f:
            digest.update(line)
            panel,st,i,w,lead,g,h,d,v,live=json.loads(line)
            b,a,targets=from_raw(d,v)
            assert len(b)==18 and a
            path=profile(b,a)
            panels[panel][path]+=1
            reference=C.inversemod(a,b)
            for p in targets:
                pp=padded(p,17)
                u=action(b,a,pp)
                assert u==padded(C.div(C.mul(reference,p),b)[1],17)
                assert action(b,a,u,True)==pp
                checks+=1
    hist={p:[dict(degrees=k,count=v,**cost(k)) for k,v in sorted(h.items(),key=lambda kv:(-kv[1],kv[0]))] for p,h in panels.items()}
    cohort=sum(panels.values(),collections.Counter())
    out=dict(raw_sha256=digest.hexdigest(),cases=sum(cohort.values()),forward_inverse_sector_pairs=checks,
             profiles=len(cohort),panels=hist,
             total_profiles=[dict(degrees=k,count=v,**cost(k)) for k,v in sorted(cohort.items(),key=lambda kv:(-kv[1],kv[0]))],
             exclusions=['Euclidean control/coefficient generation', 'in-place basis frames and temporary wiring',
                         'exact native costs of quantum scaling and cleanup', 'other adapter work'],
             static_reference_headroom=26384)
    args.out.write_text(json.dumps(out,indent=2)+'\n')
    print(out['cases'], checks, out['profiles'])
    for e in out['total_profiles'][:12]: print(e)


if __name__=='__main__':
    main()
