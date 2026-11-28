# Prepare and run mitm.exe, then recheck exactly and write the cover with two forced five-care columns.
# usage: mitm.py k cover.pkl out_cover.pkl [limit_seconds] [seed] [threads]
import sys, pickle, subprocess, time, os
from common import *
from frame import *
from fivecol import prep
from fivecols import build_candidates, State

NO = 30


def main(k, cover_file, out_file, limit=3000, seed=1, threads=6):
    t0 = time.time()
    F = Frame(k)
    cov = pickle.load(open(cover_file, 'rb'))
    cov, z = prep(F, cov)
    n = len(cov)
    full = F.full
    five = [y for y in range(F.ny) if len(F.carex[y]) == 5]
    lin = [np.ones(F.ny, np.uint8)] + [F.ybits[t] for t in range(len(F.Y))] + list(F.tagf)
    if k == 0:
        lin += [np.array([((int(F.G[0, y]) >> i1) & (int(F.G[0, y]) >> i2)) & 1 for y in range(F.ny)], np.uint8) for i1, i2 in TAGS]
    D0 = []
    for y in range(F.ny):
        d = 0
        for o in range(NO):
            if F.Dg[o, 0, y]:
                d |= 1 << o
        D0.append(d)
    cands = build_candidates(F, five, lin, full)
    ys = list(cands)
    if os.environ.get('CONTROL'):            # positive control: the same column twice must be solvable
        ys = [ys[0], ys[0]]
    nc = len(cands[ys[0]])
    assert all(len(cands[y]) == nc for y in ys)
    states = {y: State(F, cov, z, full, y, cands[y], D0) for y in ys}
    cols = {y: p for p, y in enumerate(full)}
    a = [0] * n
    b = [0] * n
    for y in full:
        zv = z[y]
        for i in range(n):
            if zv >> (2 * i) & 1:
                a[i] |= 1 << cols[y]
            if zv >> (2 * i + 1) & 1:
                b[i] |= 1 << cols[y]
    s = [c[0] for c in cov]
    planes = [c[1] for c in cov]
    groups = {}
    for i, U in enumerate(planes):
        groups.setdefault(U, []).append(i)
    movable = [g for g in groups.values() if len(g) >= 2]
    mask = (1 << 64) - 1

    def words(v):
        return ' '.join(str((v >> (64 * t)) & mask) for t in range(3))
    lines = [f'{len(movable)} {len(ys)} {nc}']
    forced_pair_ok = None
    for g in movable:
        lines.append(str(len(g)))
        lines += [f'{words(a[i])} {words(b[i])} {s[i]}' for i in g]
    for y in ys:
        st = states[y]
        for c, sup in enumerate(cands[y]):
            m = 0
            for yy in sup:
                m |= 1 << cols[yy]
            o = 0
            for w in range(NO):
                o |= ((st.O[w] >> c) & 1) << w
            lines.append(f'{words(m)} {o}')
    lines.append(f'{limit} {seed} {threads}')
    print(f'k={k}: groups {sorted((len(g) for g in movable), reverse=True)}, columns {ys}, candidates {nc} ({time.time() - t0:.0f}s)', flush=True)
    r = subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get('MITM', 'mitm_all.exe'))], input='\n'.join(lines),
                       stdout=subprocess.PIPE, text=True)
    out = r.stdout.split('\n')
    print(out[0], f'({time.time() - t0:.0f}s)', flush=True)
    if not out[0].startswith('FOUND'):
        return 1
    _, y1, c1, y2, c2, npairs = out[0].split()
    y1, c1, y2, c2 = ys[int(y1)], int(c1), ys[int(y2)], int(c2)
    newS = list(s)
    for g, line in zip(movable, out[1:]):
        for i, v in zip(g, line.split()):
            newS[i] = int(v)
    newcov = [(newS[i], planes[i]) for i in range(n)]
    assert all(sv for sv, _ in newcov), 'a chip lost all outputs'
    cov2, z2 = prep(F, newcov)
    assert cov2 == newcov
    forced = {}
    if os.environ.get('CONTROL'):
        st = State(F, newcov, z2, full, y1, [cands[y1][c1], cands[y2][c2]], D0)
        zero_bits = [(st.O[w] >> b) & 1 for b in range(2) for w in range(NO)]
        print('control: both candidates satisfied on exact recheck:', not any(zero_bits), flush=True)
        return 0
    for y, c in ((y1, c1), (y2, c2)):
        sup = cands[y][c]
        st = State(F, newcov, z2, full, y, [sup], D0)
        assert st.zero() == 0, f'column {y} not satisfied on recheck'
        forced[y] = sup
    pickle.dump(newcov, open(out_file, 'wb'))
    pickle.dump(forced, open(out_file.replace('.pkl', '.five.pkl'), 'wb'))
    print(f'rechecked columns {list(forced)}; wrote {out_file}', flush=True)
    return 0


if __name__ == '__main__':
    a_ = sys.argv[1:]
    sys.exit(main(int(a_[0]), a_[1], a_[2], *map(int, a_[3:])))
