"""Structure of our loaders: special columns, product normal form, stage blocks."""
import sys
from collections import Counter
from lib import *

def analyze(k, verbose=True):
    L = Loader(k)
    # which columns x are 'special': for each product, columns where u or v is not alpha(p)+q(x) on p<76
    badx = Counter()
    for i in range(L.no):
        for G in (L.Ug[i], L.Vg[i]):
            H = G[:76]
            # separability test column by column against column 0..: find majority pattern
            D = H ^ H[:, :1]          # difference to column 0 as function of p
            for x in range(16):
                col = D[:, x]
                if not (col == col[0]).all():
                    badx[x] += 1
    # special columns: x whose difference is non-constant in p (relative to an ordinary reference)
    ref_counts = []
    for ref in range(16):
        c = 0
        for i in range(L.no):
            for G in (L.Ug[i], L.Vg[i]):
                H = G[:76]
                D = H ^ H[:, [ref]]
                c += sum(int(not (D[:, x] == D[0, x]).all()) for x in range(16))
        ref_counts.append(c)
    ref = int(np.argmin(ref_counts))
    nonsep = Counter()
    for i in range(L.no):
        for G in (L.Ug[i], L.Vg[i]):
            H = G[:76]
            D = H ^ H[:, [ref]]
            for x in range(16):
                if not (D[:, x] == D[0, x]).all():
                    nonsep[x] += 1
    special = sorted(x for x, c in nonsep.items() if c > 5)
    ordx = [x for x in range(16) if x not in special]
    x0 = ordx[0]
    # per product: mixed rank on ordinary columns (u and v must be 0 for normal form)
    uvm = Counter(); closers = []
    prod_mixed = []
    for i in range(L.no):
        mu = mixed_part(L.Ug[i], ordx, x0); mv = mixed_part(L.Vg[i], ordx, x0)
        ru = rank([bits(r) for r in mu]); rv = rank([bits(r) for r in mv])
        mp = mixed_part(L.Ug[i] & L.Vg[i], ordx, x0)
        rp = rank([bits(r) for r in mp])
        uvm[(ru, rv)] += 1
        prod_mixed.append(rp)
        if rp < 2 or ru or rv:
            closers.append((i, ru, rv, rp, int(L.FAN[i].sum())))
    # fan-out suffix ranks (over the 35 wires)
    F = [bits(L.FAN[i]) for i in range(L.no)]
    sfx = [rank(F[t:]) for t in range(L.no + 1)]
    pfx = [rank(F[:t]) for t in range(L.no + 1)]
    # fan-out support over wires
    sup = L.FAN.sum(0)
    if verbose:
        print(f"== bank {k}: no={L.no} special={special} ref={ref} nonsep={dict(nonsep)}")
        print("   (u,v) mixed ranks:", dict(uvm))
        print("   product mixed rank hist:", dict(Counter(prod_mixed)))
        print("   closers/odd products (i,ru,rv,rprod,fanweight):", closers[:20])
        drops = [(t, sfx[t]) for t in range(1, L.no + 1) if sfx[t] != sfx[t - 1]]
        print("   suffix rank at 0:", sfx[0], " drops:", drops)
        print("   fan support per word wire:", [(wn(n), int(sup[n])) for n in range(35) if sup[n]])
    return dict(special=special, closers=closers, sfx=sfx, prod_mixed=prod_mixed)

if __name__ == "__main__":
    for k in [int(a) for a in sys.argv[1:]] or WIRED:
        analyze(k)
