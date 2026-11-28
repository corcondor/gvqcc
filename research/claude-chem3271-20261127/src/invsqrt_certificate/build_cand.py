"""Apply free-monomial certificates (and the few CCZ terms) to an op list (qsim text format).
usage: python -I build_cand.py in.ops.txt out.ops.txt hmr_bit cert.txt [--strip-bit N]...
  hmr_bit: the classical bit written by the HMR whose debt the certificate pays (condition of all new ops).
  --strip-bit N: delete every op conditioned on bN and every PUSH(bN) block (only valid when bN is never set).
"""
import sys

NAMES = ['X', 'CX', 'CCX', 'CCZ', 'CSWAP', 'SWAP', 'Z', 'CZ', 'HMR', 'ZPOW', 'NEG', 'BINV', 'BST0', 'BST1', 'PUSH', 'POP']
OPC = {n: i for i, n in enumerate(NAMES)}


def load(path):
    with open(path) as f:
        n = int(f.readline())
        return [tuple(int(x) for x in f.readline().split()) for _ in range(n)]


def dump(ops, path):
    with open(path, 'w') as f:
        f.write('%d\n' % len(ops))
        for o in ops:
            f.write('%d %d %d %d %d %d\n' % o)


def written_bits(ops):
    w = set()
    for g, a, b, c, cd, ang in ops:
        n = NAMES[g]
        if n == 'HMR':
            w.add(b)
        elif n in ('BINV', 'BST1'):
            w.add(a)
    return w


def strip(ops, bit):
    out = []
    depth_skip = 0
    for o in ops:
        n = NAMES[o[0]]
        if depth_skip:
            if n == 'PUSH':
                depth_skip += 1
            elif n == 'POP':
                depth_skip -= 1
            continue
        if n == 'PUSH' and o[4] == bit:
            depth_skip = 1
            continue
        if o[4] == bit:
            continue
        out.append(o)
    return out


def op(name, a=-1, b=-1, c=-1, cond=-1, ang=0):
    return (OPC[name], a, b, c, cond, ang)


def parse_l(s):
    return [-1 if t == '1' else int(t[1:]) for t in s.split(',') if t]


def ccz_ops(l, bit):
    """CCZ of three affine forms, conditioned on bit; only Clifford basis changes around it."""
    forms = [set(x for x in lf if x >= 0) for lf in l]
    const = [lf.count(-1) & 1 for lf in l]
    used = set()
    targets = []
    pre = []
    # pick, for each form, a target wire that does not occur in any other form
    for i, fm in enumerate(forms):
        others = set()
        for j, g in enumerate(forms):
            if j != i:
                others |= g
        cands = sorted(fm - others - used)
        if not cands:
            raise SystemExit('cannot realise CCZ forms without an auxiliary wire: %r' % (l,))
        t = cands[0]
        used.add(t)
        targets.append(t)
    for i, fm in enumerate(forms):
        t = targets[i]
        for w in sorted(fm - {t}):
            pre.append(op('CX', w, t))
        if const[i]:
            pre.append(op('X', t))
    post = list(reversed(pre))
    return pre + [op('CCZ', targets[0], targets[1], targets[2], bit)] + post


def apply(ops, certs):
    """certs: list of (bit, certfile). Insert new ops before the op index given in the certificate."""
    before = {}
    for bit, path in certs:
        for line in open(path):
            p = line.split()
            if p[0] == 'MONO':
                k, i, j = int(p[1]), int(p[2]), int(p[3])
                if i < 0:
                    new = [op('NEG', cond=bit)]
                elif j < 0:
                    new = [op('Z', i, cond=bit)]
                else:
                    new = [op('CZ', i, j, cond=bit)]
            elif p[0] == 'CCZ':
                k = int(p[1])
                new = ccz_ops([parse_l(x) for x in p[2:5]], bit)
            else:
                raise SystemExit('bad line ' + line)
            before.setdefault(k, []).extend(new)
    out = []
    for i, o in enumerate(ops):
        out += before.get(i, [])
        out.append(o)
    out += before.get(len(ops), [])
    return out


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    bit = int(sys.argv[3])
    cert = sys.argv[4]
    strips = [int(sys.argv[i + 1]) for i, a in enumerate(sys.argv) if a == '--strip-bit']
    ops = load(src)
    new = apply(ops, [(bit, cert)])
    for s in strips:
        assert s not in written_bits(new), 'bit %d is written; cannot strip' % s
        new = strip(new, s)
    dump(new, dst)
    tof = sum(1 for o in new if NAMES[o[0]] in ('CCX', 'CCZ', 'CSWAP'))
    print('ops', len(new), 'static toffoli-class', tof)
