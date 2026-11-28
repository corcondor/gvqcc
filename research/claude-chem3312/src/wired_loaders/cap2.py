"""Rebuild design: block 1 = chosen native wires (searched fresh), block 2 = zero column paid by dead flips + block-1 steering.
Capacity = sum_p min(8, dim F_p) over flips invisible to block 1; need = 8*(75-39)."""
import itertools, sys
from tgt import *
from capacity import Cap

def out_basis23():
    names = [f's{j}b{b}' for j in range(5) for b in range(1, 6)]
    return [n for n in names if n not in ('s3b1', 's4b1')]
def wire_bit(s):
    return 7 * int(s[1]) + int(s[3])

def capacity_for(k, batches, block1, m=8, zeta=None):
    forb = {wire_bit(s) for s in block1}
    # flips: per cell basis vectors from spec, keep those not touching block-1 wires
    colset = set(ORDX) if zeta is None else set(zeta)
    F = [dict() for _ in range(77)]
    n_flips = 0
    for b in batches:
        for a, basis in cell_free_basis(b).items():
            p, x = a >> 4, a & 15
            if x not in colset:
                continue
            for v in basis:
                bitsv = [n for n in range(35) if v >> n & 1]
                if any((n - (1 if n % 7 == 6 else 0)) in forb for n in bitsv):
                    continue
                ins(F[p], v)
                n_flips += 1
    cap = sum(min(m, len(F[p])) for p in range(1, 76)) + min(m, len(F[0]))
    return cap, n_flips

for k in (14, 13, 8):
    print(f"== bank {k} (batch {k} only)")
    res = []
    for j1, j2 in itertools.permutations(range(5), 2):
        base = [f's{j1}b{b}' for b in range(1, 6)]
        extra_opts = [f's{j2}b{b}' for b in range(1, 6) if f's{j2}b{b}' not in ('s3b1', 's4b1')]
        base = [s for s in base if s not in ('s3b1', 's4b1')]
        need = 7 - len(base)
        for ex in itertools.combinations(extra_opts, need):
            b1 = base + list(ex)
            cap, nf = capacity_for(k, [k], b1)
            res.append((cap, b1))
    res.sort(reverse=True)
    for cap, b1 in res[:5]:
        print("   cap", cap, "block1", b1)
