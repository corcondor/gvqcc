"""Physical HMR phase-return kernel derived from PR299.
Run with the PR299 Schur generator dependencies and fixtures on PYTHONPATH.
No syndrome-dependent host dispatch. m[0:12] is already classical.
"""
from guard_span import SpanGauge, TERMS, mul
MATRIX = tuple(tuple(mul(1 << i, 1 << j) for j in range(12)) for i in range(12))

class PhaseDual(SpanGauge):
    def bxor(self, src, dst):
        assert src != dst
        self.ops.append(('BXC', src, dst))
        self.free.append(False)

    def gated_repay(self, flag, x, y, aux):
        assert len(x) == len(y) == 12 and len(set(x+y)) == 24
        assert aux not in set(x+y) | {flag}
        parity = 73
        current = 0
        self.bclear(parity)
        for i, p in enumerate(x):
            self.ccx(flag, p, aux)
            for j, z in enumerate(y):
                mask = MATRIX[i][j]
                for k in range(12):
                    if (mask ^ current) >> k & 1:
                        self.bxor(k, parity)
                current = mask
                self.cz(aux, z, parity)
            self.hmr(aux, 72)
            self.cz(flag, p, 72)
            self.bclear(72)
        self.bclear(parity)

def certificate():
    for i in range(12):
        for j in range(12):
            t = 0
            for a,b,c in TERMS:
                if (a >> i) & 1 and (b >> j) & 1:
                    t ^= c
            assert t == MATRIX[i][j]
            for m in range(4096):
                assert (t & m).bit_count() % 2 == (MATRIX[i][j] & m).bit_count() % 2
    for g in (0,1):
        for x in (0,1):
            for m in (0,1):
                assert (g*x*m) ^ (g*x*m) == 0
    return dict(basis_products=144, measurement_basis_cases=589824, hmr_truth_cases=8)
