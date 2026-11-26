import json, random
from design import *
k = 13
block1 = ['s1b1','s1b2','s1b3','s1b4','s1b5','s2b1','s2b5']
D = Design(k, block1, 'dbg13', seed=1)
D.block1()
prior = list(range(39))
flips = D.flip_list([13], D.B1)
# output-space coverage: which complement functionals are hit by no flip?
imgs = {}
for p, x, v, a, b in flips:
    ins(imgs, D.out_image(v))
print("flip image dim in complement:", len(imgs), "of", len(D.comp))
zc = D.zeta_candidates(prior, flips, outputs_dim=8, top=3000)
tried = 0
from collections import Counter
for marg, ra, cap, z in [c for c in zc if c[1] >= 37][:4] + zc[:3]:
    B2 = D.random_subspace(8)
    eqs, nvar = D.zero_system(B2, flips, prior, z)
    # rank of the masks and number of violated dependencies
    piv = {}; bad = 0; dep = 0
    for m, r in eqs:
        while m:
            t = m.bit_length() - 1
            if t in piv:
                m ^= piv[t][0]; r ^= piv[t][1]
            else:
                piv[t] = (m, r); break
        else:
            dep += 1
            bad += r
    # rows with flips per combo
    cnt = []
    for o in range(8):
        rows = 0
        for p in range(75):
            if (eqs[75*o+p][0] >> (8*39)):
                rows += 1
        cnt.append(rows)
    print(f"zeta margin {marg} rankA {ra} cap {cap}: eqs {len(eqs)} rank {len(piv)} dependencies {dep} violated {bad}; rows with flips per output {cnt}")
