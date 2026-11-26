"""Pick block 1 (7 native wires) maximising block-2 flip capacity (m=8, own batch, all ordinary columns,
preserving the next bank's combos)."""
import itertools, sys
from tgt import *

def wire_bit(s):
    return 7 * int(s[1]) + int(s[3])

def best_block1(k, batches, m=8, top=3):
    names = [f's{j}b{b}' for j in range(5) for b in range(1, 6)]
    Z = BLK[str(k)]['Z']
    # independent output wires: drop one bit-1 wire per relation
    ok_names = []
    basis = {}
    for g in Z:
        ins(basis, g)
    for s in names:
        if ins(basis, 1 << wire_bit(s)):
            ok_names.append(s)
    spec = {b: cell_free_basis(b) for b in batches}
    res = []
    for j1, j2 in itertools.permutations(range(5), 2):
        base = [s for s in ok_names if s.startswith(f's{j1}')]
        extra = [s for s in ok_names if s.startswith(f's{j2}')]
        need = 7 - len(base)
        if need < 0 or need > len(extra):
            continue
        for ex in itertools.combinations(extra, need):
            b1 = base + list(ex)
            forb = {wire_bit(s) for s in b1}
            F = [dict() for _ in range(77)]
            for b in batches:
                znext = []
                for n in (b, b + 1):
                    if n != k and n in WIRED:
                        znext += BLK[str(n)]['Z']
                for a, vecs in spec[b].items():
                    p, x = a >> 4, a & 15
                    if x not in ORDX:
                        continue
                    for v in vecs:
                        bitsv = [n for n in range(35) if v >> n & 1]
                        if any((n - (1 if n % 7 == 6 else 0)) in forb for n in bitsv):
                            continue
                        if any(bin(v & g).count('1') & 1 for g in znext):
                            continue
                        ins(F[p], v)
            cap = sum(min(m, len(F[p])) for p in range(1, 76)) + min(m, len(F[0]))
            res.append((cap, b1))
    res.sort(key=lambda t: -t[0])
    return res[:top]

if __name__ == '__main__':
    for spec in sys.argv[1:]:
        k, bs = spec.split(':')
        k = int(k); batches = [int(b) for b in bs.split(',')]
        print(k, batches, best_block1(k, batches))
