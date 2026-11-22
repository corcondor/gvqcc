# GVQCC: 15-loader broad sweep, 2026-11-23 (JST)

**Result: 0 scored Toffoli saved.** Baseline public 33.17023 = 3357 Toffoli/pass on 15 ANGLE KMBs, 128 Q/bank. No new official leaderboard score, and no unchanged official verifier run was made.

Real-KMB sweep: 155 unique SHA-256 circuit files in 11 families; each tested on 1219 reachable addresses **both forward and reverse**, including expected output, zero scratch, symbolic HMR phase corrections (377,890 row-direction checks). Custom independent verifier, **not** official Kickmix verification.

| Family | number of KMB | total T on covered banks | total CX on covered banks |
|---|---:|---:|---:|
| published baseline | 15 | 3357 | 507303 |
| commuting CX | 15 | 3357 | **411037** |
| classical measurement-bit latch | 15 | 3357 | 507303 |
| safe HMR retiming | 15 | 3357 | 507303 |
| unique HMR classical bits | 10 wired banks | 2152 | 301609 |
| unique bits + HMR retiming | 10 wired banks | 2152 | 301609 |
| negative-control CCX identity | 15 | 3357 | 507318 |
| CCX to CSWAP Fredkin identity | 15 | 3357 | 507333 |
| latch + CX | 15 | 3357 | 413851 |
| neg control + CX | 15 | 3357 | 411052 |
| Fredkin + CX | 15 | 3357 | 411067 |

**Important:** 10-bank T=2152 is for the 10 covered banks, not all 15. All complete 15-bank families remained 3357 T. CX reduction by 96266 = 18.98% is real but unscored.

Searches that returned zero score-relevant candidate:
- All 15 banks: fixed-cache output product local 2->1, 3->2, 4->3 replacements: 0.
- Wired banks k2,k4,k8,k10,k13,k14: 150 random rank-6 dependent 7-term groups per bank, tested 7->6: 0 (900 trials, not a lower bound).
- HMR bit latches and forward retiming in wired banks: no scratch reused before its final nonlinear use in tested schedule.
- Replacement of one CCX by Fredkin (CSWAP) has cost 1T still, not free.

Angle table discovery: in each wired bank k2,k3,k4,k6,k8,k9,k10,k12,k13,k14, exactly bit positions 0,7,14,21,28 are affine across each of the 76 complete 16-row lower-address blocks. Preserve / exploit this low-degree code structure in candidate reparameterizations; do not optimize affine discrepancy as an end in itself.

**Top priority:** joint regenerate the cache AND products and the entire nonlinear output tail, i.e., create new KMB, not alter CX count only. Previous published k8 213->211 compared: 74/82 scratch products identical, 8 changed, output product count 131->129, no identical output products. A fixed-cache local rewrite is not enough by this restricted search evidence. Next independently develop (A) matroid parity/FWHT cache-tail compiler, (B) different reversible compute/uncompute lifetime schedule with true Q<=128, (C) angle-table sign-gauge + code-aware joint compiler with exact Givens numerical acceptance.

Exact 155 KMBs, local verifier, SHA manifest and all result JSON are provided in the assistant's delivered ZIP: `GVQCC_3357_BROAD_REVERSIBLE_HMR_20261123.zip` (conversation attachment, not in repo). Source credit in ZIP. Public source and all15 fetched and pinned in [GitHub Actions 45050045572](https://github.com/corcondor/gvqcc/actions/runs/45050045572). No Kaggle submission was performed.

Claude can run this as independent source check, but no Claude runtime is linked to the assistant. Required submission of an improvement: changed .kmb, SHA, script, scored T count, all reachable inputs forward+reverse, scratch+phase, preferably unchanged official verifier, and score delta. No gain? report negative code and scope. No false optimality claims.
