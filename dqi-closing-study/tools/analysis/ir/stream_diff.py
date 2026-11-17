"""Two circuits of one lineage aligned instruction by instruction: where they differ, and by how many Toffoli-likes.

For files that ship without a generator (the dqi 890 line: two public patch sets on one parent), the difference of
two files is the patch itself. Each instruction gets a 64-bit key from its type and every operand (qubits, target
bit, condition bit, an angle's words), so equal keys are equal instructions; the two key streams are aligned by
walking their common runs and, at a mismatch, re-synchronising on the nearest pair of positions whose next GRAM
instructions are equal (searched in a window that grows fourfold until one is found). A region is a stretch
A[a0:a1] against B[b0:b1] between two common runs.

Prints the regions' count, the instructions and static Toffoli-likes inside them on each side, the regions grouped
by (Toffoli-likes in A, in B), and the first --list of them. The alignment is a diff, not a least one: a
re-synchronisation on a repeated stretch can split one patch in two (regions closer than GRAM are merged).

    python analysis/ir/stream_diff.py A.kmb B.kmb [--gram 48] [--list 20] [--save OUT.json]
    python analysis/ir/stream_diff.py A.kmb B.kmb --splice OUT.kmb --from-b TA,TB
                                      A with the patches (regions closer than 4,000 instructions) that hold a
                                      region of TA Toffoli-likes in A against TB in B taken from B: two patch sets
                                      on one parent merged. The result is a candidate: its check is the verifier.
    python analysis/ir/stream_diff.py A.kmb B.kmb --transplant C.kmb OUT.kmb --from-b TA,TB
                                      the patch of A -> B (its first cluster holding that signature) carried to
                                      every stretch of C whose op types equal the patch's old stretch up to
                                      insertions in its common runs, on that stretch's own wires (transplant())
    python analysis/ir/stream_diff.py --types A.kmb A0 A1 --pieces LO,HI ... --in B.kmb ...
                                      where pieces of the stretch A[A0:A1] recur in other files by op types alone
    python analysis/ir/stream_diff.py --plant CIRCUIT.kmb      a file against itself (no region) and against a copy
                                                               with one stretch deleted and one doubled (two
                                                               regions at the planted bounds)
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from qc import ir  # noqa: E402

MUL = [np.uint64(x) for x in (0x9E3779B97F4A7C15, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0x27D4EB2F165667C5,
                              0x85EBCA77C2B2AE63, 0xFF51AFD7ED558CCD, 0xC4CEB9FE1A85EC53, 0x2545F4914F6CDD1D,
                              0xD6E8FEB86659FD93, 0xA0761D6478BD642F, 0xE7037ED1A0B428DB)]


def keys(c, chunk=8_000_000):
    """One uint64 per instruction, from its type and all its operands."""
    n = c.num_ops
    out = np.empty(n, np.uint64)
    off = {nm: 0 for nm in ir._PACKETS}
    with np.errstate(over='ignore'):
        for a in range(0, n, chunk):
            t = np.asarray(c.types[a:a + chunk])
            k = t.astype(np.uint64) * MUL[0]
            for j, nm in enumerate(('qqq0', 'qqq1', 'qqq2', 'qq0', 'qq1', 'q0', 'b0', 'bc')):
                m = ir._lut_of(nm)[t]
                cnt = int(m.sum())
                if cnt:
                    k[m] ^= (np.asarray(getattr(c, nm)[off[nm]:off[nm] + cnt]).astype(np.uint64) + np.uint64(j + 1)) * MUL[j + 1]
                    off[nm] += cnt
            m = ir.LANGLE[t]
            cnt = int(m.sum())
            if cnt:
                ang = np.asarray(c.angles[off['angles']:off['angles'] + cnt]).astype(np.uint64)
                k[m] ^= ang[:, 0] * MUL[9] ^ ang[:, 1] * MUL[10]
                off['angles'] += cnt
            k ^= k >> np.uint64(29)
            k *= MUL[5]
            k ^= k >> np.uint64(32)
            out[a:a + chunk] = k
    return out


def first_mismatch(a, b, chunk=4_000_000):
    """The length of the common prefix of two key arrays."""
    m = min(len(a), len(b))
    for s in range(0, m, chunk):
        d = np.flatnonzero(a[s:min(s + chunk, m)] != b[s:min(s + chunk, m)])
        if len(d):
            return s + int(d[0])
    return m


def gram_hash(x, W, R):
    with np.errstate(over='ignore'):
        return np.lib.stride_tricks.sliding_window_view(x, W) @ R


def align(ka, kb, W=48, window=4096, log=print):
    """[(a0, a1, b0, b1)]: the differing stretches between the common runs of two key streams."""
    R = np.random.default_rng(7).integers(1, 1 << 62, W, dtype=np.int64).astype(np.uint64) * np.uint64(2) + np.uint64(1)
    i = j = 0
    regions = []
    while True:
        k = first_mismatch(ka[i:], kb[j:])
        i, j = i + k, j + k
        if i == len(ka) or j == len(kb):
            if i < len(ka) or j < len(kb):
                regions.append((i, len(ka), j, len(kb)))
            break
        N, found = window, None
        while found is None:
            a, b = ka[i:i + N], kb[j:j + N]
            if len(a) >= W and len(b) >= W:
                ha, hb = gram_hash(a, W, R), gram_hash(b, W, R)
                _, ia, ib = np.intersect1d(ha, hb, return_indices=True)
                for t in np.argsort(ia + ib)[:64]:
                    if (a[ia[t]:ia[t] + W] == b[ib[t]:ib[t] + W]).all():
                        found = (int(ia[t]), int(ib[t]))
                        break
            if found is None:
                if N >= max(len(ka) - i, len(kb) - j):
                    break
                N *= 4
        if found is None:
            regions.append((i, len(ka), j, len(kb)))
            break
        regions.append((i, i + found[0], j, j + found[1]))
        i, j = i + found[0], j + found[1]
    merged = []
    for r in regions:                                       # regions closer than W: one patch split by a repeat
        if merged and r[0] - merged[-1][1] < W:
            merged[-1] = (merged[-1][0], r[1], merged[-1][2], r[3])
        else:
            merged.append(r)
    return merged


def report(A, B, pa, pb, W, nlist, save=None, log=print):
    t0 = time.time()
    ka, kb = keys(A), keys(B)
    regions = align(ka, kb, W)
    ta, tb = ir.LTOF[np.asarray(A.types)], ir.LTOF[np.asarray(B.types)]
    ca, cb = np.concatenate([[0], np.cumsum(ta)]), np.concatenate([[0], np.cumsum(tb)])
    rows = [(a0, a1, b0, b1, int(ca[a1] - ca[a0]), int(cb[b1] - cb[b0])) for a0, a1, b0, b1 in regions]
    opsA, opsB = sum(r[1] - r[0] for r in rows), sum(r[3] - r[2] for r in rows)
    tofA, tofB = sum(r[4] for r in rows), sum(r[5] for r in rows)
    log(f'{pa} ({A.num_ops:,} instructions, {int(ca[-1]):,} static Toffoli-likes) against {pb} ({B.num_ops:,}, '
        f'{int(cb[-1]):,}): {len(rows)} regions; inside them {opsA:,} instructions and {tofA:,} Toffoli-likes in A, '
        f'{opsB:,} and {tofB:,} in B (B - A = {tofB - tofA:+,}; the files\' totals differ by {int(cb[-1] - ca[-1]):+,})  '
        f'[{time.time() - t0:.0f} s]')
    sig = Counter((r[4], r[5]) for r in rows)
    log('  regions by (Toffoli-likes in A, in B): ' + ', '.join(f'({x}, {y}) x {n}' for (x, y), n in sig.most_common(24)))
    for r in rows[:nlist]:
        log(f'  A {r[0]:,}-{r[1]:,} ({r[1] - r[0]} ops, {r[4]} Toffoli-likes) | B {r[2]:,}-{r[3]:,} ({r[3] - r[2]} ops, {r[5]})')
    if save:
        Path(save).write_text(json.dumps({'A': pa, 'B': pb, 'gram': W, 'regions': rows}))
    return rows


def clusters(rows, gap=4000):
    """Regions closer than `gap` instructions (in A) as one patch: [[region, ...], ...]."""
    out = [[rows[0]]] if rows else []
    for r in rows[1:]:
        if r[0] - out[-1][-1][1] < gap:
            out[-1].append(r)
        else:
            out.append([r])
    return out


def splice(A, B, rows, sig, out_path, log=print):
    """A with every patch (cluster of regions) that holds a region of signature `sig` = (Toffoli-likes in A, in B)
    taken from B instead; every other difference stays A's. A classical bit that B's stretch writes and A's does not
    (a new outcome of B's patch) gets a fresh id past both files' bits, so it cannot meet a bit A's own patches
    made. Prints what it checks: the clusters' shapes, the bits each B stretch reads from outside against A's."""
    import dataclasses
    cl = [c for c in clusters(rows) if any((r[4], r[5]) == sig for r in c)]
    shapes = Counter((len(c), sum(r[4] for r in c), sum(r[5] for r in c)) for c in cl)
    log(f'  {len(cl)} clusters hold a {sig} region; by (regions, Toffoli-likes in A, in B): '
        + ', '.join(f'{k} x {n}' for k, n in shapes.items()))
    spans = {c[0][0]: (c[-1][1], c[0][2], c[-1][3]) for c in cl}
    cuts = sorted({x for a0, (a1, _, _) in spans.items() for x in (a0, a1)})
    nxt = max(A.num_bits, B.num_bits)
    parts, fresh, ext_only_b = [], 0, 0
    for a, b, piece in A.pieces(cuts, allow_open=True):
        if a in spans and spans[a][0] == b:
            _, b0, b1 = spans[a]
            pb = B.slice(b0, b1, allow_open=True)
            wa, wb = set(np.unique(piece.b0).tolist()), set(np.unique(pb.b0).tolist())
            new = sorted(wb - wa)
            ext_only_b += len((set(np.unique(pb.bc).tolist()) - wb) - (set(np.unique(piece.bc).tolist()) - wa))
            old = np.array(new, dtype=np.int64)
            to = np.arange(nxt, nxt + len(new), dtype=np.int64)
            nxt, fresh = nxt + len(new), fresh + len(new)

            def remap(x):
                x = np.asarray(x).astype(np.int64)
                if not len(old) or not len(x):
                    return x.astype(np.uint32)
                k = np.searchsorted(old, x)
                hit = (k < len(old)) & (old[np.minimum(k, len(old) - 1)] == x)
                return np.where(hit, to[np.minimum(k, len(old) - 1)], x).astype(np.uint32)

            parts.append(dataclasses.replace(pb, b0=remap(pb.b0), bc=remap(pb.bc)))
        else:
            parts.append(piece)
    merged = ir.Circuit.concat(parts)
    merged.write(out_path)
    log(f'  spliced: {merged.num_ops:,} instructions, {merged.toffoli_like():,} static Toffoli-likes (A {A.toffoli_like():,}, '
        f'B {B.toffoli_like():,}), {merged.num_qubits} qubits, {merged.num_bits:,} classical bits; {fresh} bits renumbered; '
        f'bits a B stretch reads from outside that A\'s stretch does not: {ext_only_b}; sha256 {merged.sha256()[:8]} -> {out_path}')
    return merged


def _ops(c, a, b):
    return [(n, tuple(int(x) for x in q), tb, cb) for _, n, q, tb, cb in c.decode(a, b)]


def transplant(A, B, C, rows, sig, out_path, head=300, log=print):
    """A patch carried to sites an exact matcher misses. The template is the first cluster of regions that holds a
    `sig` region: its old stretch in A and its new one in B. A site in C is a stretch whose op types equal the
    template's old stretch from its leading run of HMRs on, up to instructions inserted inside the common runs (a
    site's own extra work, kept). At a site the regions' new text is written on the site's own wires:
      - one map from the template's wires to the site's, read position by position on the common runs (refused
        unless it is a function and one to one);
      - the leading HMRs (the stretch's entry wires, whose order carries the mask's bit order) by their own
        positions;
      - a helper the new text uses and no common run touches goes to an entry wire the common runs leave alone
        (clean after its HMR and idle to the stretch's end);
      - a bit the new text writes gets a fresh id; a bit it reads from outside goes where the site's old text reads
        it at the same position.
    Everything else in C stays. The result is a candidate: its check is the verifier, on the classes each site
    meets."""
    cl = [c for c in clusters(rows) if any((r[4], r[5]) == sig for r in c)][0]
    s0, e0 = cl[0][0], cl[-1][1]
    L = e0 - s0
    regs = [(r[0] - s0, r[1] - s0, r[2], r[3]) for r in cl]
    in_region = np.zeros(L + 1, bool)
    for ra, rb, _, _ in regs:
        in_region[ra:rb] = True
    tO, tC = bytes(np.asarray(A.types[s0:e0])), bytes(np.asarray(C.types))
    Oj = _ops(A, s0, e0)
    hreg = next(r for r in cl if (r[4], r[5]) == sig)
    hoff = hreg[0] - s0
    piece = tO[hoff:hoff + head]
    cands, i = [], tC.find(piece)
    while i >= 0:
        cands.append(i)
        i = tC.find(piece, i + 1)
    newops = [_ops(B, rc, rd) for _, _, rc, rd in regs]
    new_written = {tb for ops in newops for _, _, tb, _ in ops if tb is not None}
    new_ext = {cb for ops in newops for _, _, _, cb in ops if cb is not None} - new_written
    nxt = max(A.num_bits, B.num_bits, C.num_bits)
    sites, plan = [], {}
    for hc in cands:
        g0 = hc - hoff
        while g0 > 0 and not ((tC[g0] & 0x7F) == 0x50 and (tC[g0 - 1] & 0x7F) != 0x50
                              and all((tC[g0 + d] & 0x7F) == 0x50 for d in range(8))):
            g0 -= 1
            if hc - g0 > hoff + 2000:
                break
        seg = tC[g0:g0 + L + 2000]
        ins, ok, x, y = [], True, 0, 0                      # a linear walk: equal runs, and insertions in seg
        while x < L:                                        # found by re-synchronising on the next 64 op types
            if y < len(seg) and tO[x] == seg[y]:
                x, y = x + 1, y + 1
                continue
            n = next((d for d in range(1, 600) if seg[y + d:y + d + 64] == tO[x:x + 64]), None)
            if n is None or in_region[x] or (x > 0 and in_region[x - 1]) or sum(m for _, m in ins) + n > 1500:
                ok = False
                break
            ins.append((x, n))
            y += n
        if not ok:
            continue
        tot = sum(n for _, n in ins)
        Gk = _ops(C, g0, g0 + L + tot)

        def kpos(x):
            return x + sum(n for i1, n in ins if i1 < x)

        qmap, bold, bad = {}, {}, 0
        for off in range(L):
            (n1, q1, tb1, cb1), (n2, q2, tb2, cb2) = Oj[off], Gk[kpos(off) if not any(i1 == off for i1, _ in ins)
                                                                 else kpos(off) + dict(ins)[off]]
            assert n1 == n2, (off, n1, n2)
            for x, y in ((tb1, tb2), (cb1, cb2)):
                if x is not None:
                    bold.setdefault(x, y)
            if in_region[off]:
                continue
            for x, y in zip(q1, q2):
                bad += qmap.setdefault(x, y) != y
        if bad or len(set(qmap.values())) != len(qmap):
            log(f'  site at {g0:,}: the common runs give no one-to-one wire map ({bad} conflicts): skipped')
            continue
        nh = 0
        while nh < len(newops[0]) and newops[0][nh][0] == 'HMR' and Oj[nh][0] == 'HMR':
            nh += 1
        tmap = {Oj[d][1][0]: Gk[d][1][0] for d in range(nh)}        # the entry wires, by position
        used = set(qmap.values())
        spare = [w for w in tmap.values() if w not in used]
        helpers = sorted({q for ri, ops in enumerate(newops) for oi, (_, qs, _, _) in enumerate(ops)
                          for q in qs if not (ri == 0 and oi < nh) and q not in qmap})
        if len(helpers) > len(spare) or not new_ext <= set(bold):
            log(f'  site at {g0:,}: {len(helpers)} helpers for {len(spare)} spare entry wires, outside bits unmapped '
                f'{len(new_ext - set(bold))}: skipped')
            continue
        hmap = dict(zip(helpers, spare))
        fresh = {}
        parts_ops = []
        for ri, ops in enumerate(newops):
            out = []
            for oi, (n, qs, tb, cb) in enumerate(ops):
                if ri == 0 and oi < nh:
                    qs2 = tuple(tmap[q] for q in qs)
                else:
                    qs2 = tuple(qmap[q] if q in qmap else hmap[q] for q in qs)
                if tb is not None and tb not in fresh:
                    fresh[tb] = nxt
                    nxt += 1
                tb2 = fresh[tb] if tb is not None else None
                cb2 = None if cb is None else fresh[cb] if cb in fresh else bold[cb]
                out.append((n, qs2, tuple(x for x in (tb2, cb2) if x is not None)))
            parts_ops.append(out)
        sites.append(g0)
        plan[g0] = (L + tot, ins, [(g0 + kpos(ra), g0 + kpos(rb)) for ra, rb, _, _ in regs], parts_ops)
        log(f'  site at {g0:,}: {len(ins)} insertions kept ({tot} instructions), wire map of {len(qmap)}, '
            f'{len(helpers)} helpers placed, {len(fresh)} fresh bits')
    cuts = sorted({x for g0 in sites for a, b in plan[g0][2] for x in (a, b)})
    repl = {a: (b, ops) for g0 in sites for (a, b), ops in zip(plan[g0][2], plan[g0][3])}
    parts = []
    for a, b, piece_c in C.pieces(cuts, allow_open=True):
        if a in repl and repl[a][0] == b:
            if repl[a][1]:
                parts.append(ir.Circuit.from_ops(repl[a][1], C.registers))
        else:
            parts.append(piece_c)
    new = ir.Circuit.concat(parts)
    new.write(out_path)
    log(f'  transplanted at {len(sites)} sites: {new.num_ops:,} instructions, {new.toffoli_like():,} static Toffoli-likes '
        f'(before {C.toffoli_like():,}), {new.num_qubits} qubits, {new.num_bits:,} bits; sha256 {new.sha256()[:8]} -> {out_path}')
    return new


def plant(path):
    c = ir.Circuit.read(path)
    n = c.num_ops
    fails = 0
    rows = report(c, c, 'the file', 'itself', 48, 0, log=lambda *_: None)
    print(f'plant, a file against itself: {len(rows)} regions (want 0)')
    fails += len(rows) != 0
    d0, d1, u0, u1 = n // 4, n // 4 + 137, n // 2, n // 2 + 59
    mask = np.ones(n, bool)
    mask[d0:d1] = False
    parts = [p for _, _, p in c.pieces([u1], allow_open=True)]
    dup = c.slice(u0, u1, allow_open=True)
    doubled = ir.Circuit.concat([parts[0], dup, parts[1]])
    keepm = np.ones(doubled.num_ops, bool)
    keepm[d0:d1] = False
    b = doubled.keep(keepm)
    rows = report(c, b, 'the file', 'a copy with ops deleted and doubled', 48, 0, log=lambda *_: None)
    got = [(r[0], r[1], r[2], r[3]) for r in rows]
    ok = len(got) == 2 and got[0][1] - got[0][0] == d1 - d0 and got[0][3] == got[0][2] \
        and got[1][1] == got[1][0] and got[1][3] - got[1][2] == u1 - u0
    print(f'plant, {d1 - d0} ops deleted at {d0:,} and {u1 - u0} doubled at {u1:,}: regions {got} '
          f'(want one of {d1 - d0} ops in A and none in B, one of none in A and {u1 - u0} in B): {"PASS" if ok else "FAIL"}')
    fails += not ok
    print(f'RESULT stream_diff plant: {"PASS" if not fails else "FAIL"}')
    return fails


def by_types(pa, a0, a1, pieces, targets):
    """Where a stretch of A recurs in other files by its op types alone (operands ignored): a gadget emitted on
    other wires, or left unmatched by an exact transplant. pieces: (lo, hi) offsets inside A[a0:a1]."""
    A = ir.Circuit.read(pa)
    old = bytes(np.asarray(A.types[a0:a1]))
    print(f'{pa} ops {a0:,}-{a1:,}: {a1 - a0:,} instructions, {int(ir.LTOF[np.frombuffer(old, np.uint8)].sum())} Toffoli-likes')
    hay = {p: bytes(np.asarray(ir.Circuit.read(p).types)) for p in targets}
    for lo, hi in pieces:
        piece = old[lo:hi]
        tof = int(ir.LTOF[np.frombuffer(piece, np.uint8)].sum())
        for p, h in hay.items():
            hits, i = [], h.find(piece)
            while i >= 0:
                hits.append(i)
                i = h.find(piece, i + 1)
            print(f'  offsets {lo}-{hi} ({tof} Toffoli-likes): {len(hits)} occurrences in {p}; first at {hits[:6]}, last at {hits[-2:]}')
    print(f'RESULT stream_diff types: {len(pieces)} pieces searched in {len(targets)} files')


def main():
    a = sys.argv[1:]
    if '--plant' in a:
        sys.exit(plant(a[a.index('--plant') + 1]))
    if '--transplant' in a:   # A.kmb B.kmb --transplant C.kmb OUT.kmb --from-b TA,TB: the patch of A -> B carried to C
        k = a.index('--transplant')
        paths = [x for x in a[:k] if x.endswith('.kmb')]
        A, B, C = ir.Circuit.read(paths[0]), ir.Circuit.read(paths[1]), ir.Circuit.read(a[k + 1])
        rows = report(A, B, paths[0], paths[1], 48, 0)
        sig = tuple(int(z) for z in a[a.index('--from-b') + 1].split(','))
        new = transplant(A, B, C, rows, sig, a[k + 2])
        print(f'RESULT stream_diff transplant: {C.toffoli_like() - new.toffoli_like()} static Toffoli-likes fewer in {a[k + 2]}')
        return
    if '--types' in a:        # --types A.kmb A0 A1 --pieces LO,HI ... --in B.kmb ...
        k = a.index('--types')
        pieces = [tuple(int(z) for z in x.split(',')) for x in a[a.index('--pieces') + 1:a.index('--in')]]
        return by_types(a[k + 1], int(a[k + 2]), int(a[k + 3]), pieces, a[a.index('--in') + 1:])
    paths = [x for x in a if x.endswith('.kmb')]
    W = int(a[a.index('--gram') + 1]) if '--gram' in a else 48
    nlist = int(a[a.index('--list') + 1]) if '--list' in a else 20
    save = a[a.index('--save') + 1] if '--save' in a else None
    A, B = ir.Circuit.read(paths[0]), ir.Circuit.read(paths[1])
    rows = report(A, B, paths[0], paths[1], W, nlist, save)
    if '--splice' in a:
        sig = tuple(int(z) for z in a[a.index('--from-b') + 1].split(','))
        splice(A, B, rows, sig, a[a.index('--splice') + 1])
    print(f'RESULT stream_diff: {len(rows)} regions, B - A = {sum(r[5] - r[4] for r in rows):+,} static Toffoli-likes')


if __name__ == '__main__':
    main()
