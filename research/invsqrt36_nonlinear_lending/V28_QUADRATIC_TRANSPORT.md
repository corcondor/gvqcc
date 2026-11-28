# V28 — moving quadratic chart transport across HMR
Research only; NOT SUBMISSION. V27 source SHA256 bd91d88909de18643262178477ca813c67dbcb2edc3325a99e66c964d6758258, 53,416 commands, E=22501/16. Reused exact chart.pkl (321 charts, 44,511 covered source instructions) from V27. No main or Kaggle changes. Older ANGLE archive audit remains incomplete; no global novelty claim.

## Exact native experiments
- Random 512-sample raw single-product relations: 40 proposed/0 accepted. Adding HMR-aware pivot transitions: 51 proposed/8 accepted, 251 source instructions, +14 expected paid. These screens suffered false sample relations; do not repeat.
- Structured 4096 samples (low/high x, powers of two and random x) plus exact prefilter: 9,225 gap/boundary cuts, 5,506 distinct sampled states, 12,492 candidate relations over cuts, 3,448 cuts with quadratic-only candidates, 6,965 distinct exact relation tests, all passed. Dynamic program on omitted pivots and HMR transitions: 13/13 exact bridges, 461 source instructions, +24 expected paid. Fused source X/CX/CCX and coordinate exchange screen gives same 13/461/+24.
- Propagate exact quadratic relations by inverse substitution through unconditional reversible gates, conservatively across guarded gates, and eliminate/reset at HMR boundaries. Two forward/backward passes, bounded XOR combinations, alternating-form rank factorization for native CCX synthesis. 33,115 retained relation occurrences, 19,194 multi-quadratic-monomial occurrences; 44 proposed/44 exact accepted, 1,942 source commands covered, +111.5 expected if all adopted. This is not a paid saving.
- One cost-neutral bridge [17228,17235), entry omitted q11=q17 XOR q20, exit omitted q6=0 after HMR record844. Source 7 commands/1 paid -> 10 commands/1 paid. Omit CCX and CX writing virtual q11; measure retained q6; reconstruct q11 in freed slot and exchange mapping. The direct *alternate measured representative* rule (measuring a different wire and compensating phase) was implemented, but zero accepted final paths used that specific rule. No claim of direct measurement substitution gain.
- 0-budget integration: 44,518/53,416 source coverage (83.3421%), 320 merged charts, 54,063 commands, E=22501/16/static1551, 6,723 full-occupancy cuts, SHA256 717ad52507a03a8bc5d0ac16448a5ace0359ef151ae9d3e0fca59ee342981df0.
- Budgeted knapsack (frozen 36Q break-even budget 731/16): 16 selected gaps, 1,174 new source commands, 45,685/53,416 (85.5268%), 305 merged charts; longest [44205,53416), 9,211 source commands. 54,148 native commands, E=23229/16=1451.8125 (+45.5), static1606, 5,567 full-occupancy cuts. SHA256 0a88508af036b1e52086d7c65ed710faf2d8ac4dd21220cd0a874cd3c84e44d3.
- Fresh independent replay of both serialized hybrid KMBs against V27 source: all 3,133,452 legal inputs and 1,276 independent HMR outcomes; all chart boundary data, phase, rotations, classical records, guard, omitted physical line zero, terminal state, cost verified. Both still peak37Q; neither partial longest36 circuit is a complete oracle. No official verifier/score update.

## Mathematical construction
Chart relation R(q)=0 is a Boolean polynomial of degree at most two; pivot d occurs only linearly. For a source involution G, transport R to R∘G. At unconditional HMR, retain relations independent of measured bit, propagate reset relation forward, and set measured coordinate to zero in backward relations. For q_d=q_e XOR h, a fused update q_d ^= g followed by pivot exchange requires q_e ^= h XOR g. HMR representative change requires phase m*q_d=m*q_e XOR m*h and an independently valid post-measurement decoder for q_e. The latter condition is essential; phase equality alone does not establish a legal measurement substitution. Quadratic rank factorization via uv+uB+vA=(u+A)(v+B)+AB over GF(2) eliminates a pivot pair; synthesize products using reversible CNOT conjugation. Lean proves these identities and the concrete projected [17228,17235) bridge, not full reachable BDD execution.

## Frozen score model from PR43/V27
37Q E=1406.3125 gives 33.1703164053. 36Q at same E would give 33.4746482342. Budgeted hybrid currently 37Q predicts 32.8703142911, at 36Q would give 33.1718936533. Only 0.24140236 expected paid headroom remains in this budgeted branch before break-even. Prefer low-cost branch for further optimization; use budgeted branch as structural diagnostic, not a score improvement.

## Literature use
- Yang & Yuan, MBUndo, https://arxiv.org/html/2611.02345v1 §2.3, §4.2 Alg.4: interval last-use criterion and per-write phase corrections. Generalized here to virtual coordinates and explicitly checked HMR branch phase and record. Not their original benchmark replication.
- Amy & Lunderville, https://doi.org/10.1145/3704873 §4–5: affine/nonlinear relations; here exact sparse polynomial substitution plus BDD, not their Gröbner implementation.
- Khattar & Gidney, https://arxiv.org/html/2407.17966v2 §3: conditional cleanliness requires consumption under predicate and restoration of borrowed workspace. Here use unconditional chart/reset relations, not their full conditional-clean ladder algorithm.
- Kornerup, Sadun, Soloveichik, https://doi.org/10.22331/q-2025-02-18-1636: spooky pebble game separates classical and quantum space; motivates measuring a retained representative and later settling phase debt. No use of their asymptotic bound as a concrete circuit count.
- Quist & Laarman, https://doi.org/10.46298/lmcs-21(4:29)2025: SAT-based pebbling strategies; budget DP here is a restricted chart-path solver, not full SAT spooky pebbling.
- Meuli, Soeken, De Micheli, https://doi.org/10.1038/s41534-021-00514-y: XAG synthesis and nonlinear multiplication/width trade-off; related to our quadratic rank decomposition, not a direct reproduction.

## Reproduction
Companion archive includes V27 source/engine/chart.pkl, v28_quadratic.py, v28_mbu.py, v28_exact.py, v28_fused.py, v28_transport.py, v28_integrate.py, all receipts, native KMBs and logs. Run from v25 directory with Python:
```
python v28_fused.py v27_low_lazy.kmb
python v28_transport.py
python v28_integrate.py 0 v28_zero37_NOT_SUBMISSION.kmb
python v28_integrate.py 731/16 v28_budget37_NOT_SUBMISSION.kmb
```
Keep low-cost and width-first portfolios separate. Do not count 13 raw bridges plus 44 transported bridges additively.
