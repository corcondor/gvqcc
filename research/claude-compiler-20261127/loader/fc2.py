# Prepare fivecols state, run the C++ walk (fc2.exe), and recheck + write the cover.
# usage: fc2.py k cover.pkl out_cover.pkl want [M] [restarts] [seed]
import sys, pickle, subprocess, time, os
from common import *
from frame import *
from gf2 import solve_linear
from fivecol import prep
from fivecols import build_candidates, State

NO = 30


def main(k, cover_file, out_file, want, M=20_000_000, restarts=100000, seed=1):
    t0 = time.time()
    F = Frame(k)
    cov = pickle.load(open(cover_file, 'rb'))
    cov, z = prep(F, cov)
    n = len(cov)
    full = F.full
    assert len(full) <= 192
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
    pairs = [(i, j) for g in groups.values() if len(g) >= 2 for i in g for j in g if i != j]
    mask = (1 << 64) - 1

    def words(v, w):
        return ' '.join(str((v >> (64 * t)) & mask) for t in range(w))
    inp = out_file + '.fc2in'
    with open(inp, 'w') as fh:
        fh.write(f'{n} {len(ys)} {len(pairs)}\n')
        fh.write('\n'.join(f'{i} {j}' for i, j in pairs) + '\n')
        for i in range(n):
            fh.write(words(a[i], 3) + ' ' + words(b[i], 3) + '\n')
        fh.write(' '.join(map(str, s)) + '\n')
        for y in ys:
            st = states[y]
            C = len(cands[y])
            W = (C + 63) // 64
            fh.write(f'{C} {W}\n')
            for p in range(144):
                fh.write(words(st.member[p] if p < len(st.member) else 0, W) + '\n')
            for v in st.aS:
                fh.write(words(v, W) + '\n')
            for v in st.bS:
                fh.write(words(v, W) + '\n')
            for v in st.O:
                fh.write(words(v, W) + '\n')
    print(f'k={k}: five columns {ys}, candidates {[len(cands[y]) for y in ys]}, {len(pairs)} move pairs ({time.time() - t0:.0f}s)', flush=True)
    r = subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fc2.exe'), inp, str(want), str(M),
                        str(restarts), str(seed)], stdout=subprocess.PIPE, text=True)
    lines = r.stdout.split('\n')
    print(lines[0], f'({time.time() - t0:.0f}s)', flush=True)
    if not lines[0].startswith('FOUND'):
        return 1
    newS = [int(x) for x in lines[1].split()]
    newcov = [(newS[i], planes[i]) for i in range(n)]
    assert all(sv for sv, _ in newcov)
    cov2, z2 = prep(F, newcov)
    assert cov2 == newcov
    forced = {}
    for line in lines[2:]:
        if not line.strip():
            continue
        q, c = map(int, line.split())
        y = ys[q]
        sup = cands[y][c]
        st = State(F, newcov, z2, full, y, [sup], D0)
        assert st.zero() == 0, f'column {y} not satisfied on recheck'
        forced[y] = sup
    pickle.dump(newcov, open(out_file, 'wb'))
    pickle.dump(forced, open(out_file.replace('.pkl', '.five.pkl'), 'wb'))
    print(f'rechecked {len(forced)} columns {list(forced)}; wrote {out_file}', flush=True)
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    sys.exit(main(int(args[0]), args[1], args[2], int(args[3]), *map(int, args[4:])))
