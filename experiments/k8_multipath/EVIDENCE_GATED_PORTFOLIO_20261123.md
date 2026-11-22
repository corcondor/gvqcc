# GVQCC evidence-gated independent experiment portfolio — 2026-11-23

## Purpose and measurement
Goal: produce valid low-cost **real KMB**, then a lower **official** Kaggle score cost / higher leaderboard score. Public reference: 33.17023 with ANGLE loaders total 3357 Toffoli/pass, k8=211T/128Q. Preserve source files and author credits. A KMB with fewer unscored CX or prettier ANF does **not** count as progress toward the score.

**Do not start another mass random-seed sweep inside the fixed 197T high/low tensor template.** Its demonstrated lower bound is >=260T, greater than the 211T reference, so it cannot win regardless of seed count. Negative fixed-cache experiments (155 verified score-neutral KMBs, GF2 limited 2->1/3->2/4->3 with zero improvements) are not to be duplicated without changing the search space.

## Four independent research hypotheses, not four versions of the same neighborhood

| ID | Direct evidence | Manipulation/causal test | Hard gate to proceed |
|---|---|---|---|
| A. Nonlinear high-cache replacement + full tail recompilation | Old 213T vs public 211T had 74/82 unchanged scratch products and 8 changed products, output tail 131->129; in k8, last 8 cache values are used in 88-102 output-control expressions | Baseline: fixed old/new cache values, same compiler on both; replace AND products genuinely *outside old cache GF2 span*, resynthesize complete output tail under max 128Q. Compare with no-cache-change control, prevent copy-as-compiler | New KMB valid for arbitrary incoming word state, both traversal directions, zero scratch and phase, T<=211 reproducing baseline; candidate T<211 or bank-wide cost drop |
| B. Reversible word-register-assisted nonlinear network | Public 211T KMB uses output q11..45 as controls in 3175 CX and 6 CCX; own 661T generator uses output register as controls 0 times, 661 HMR vs public 82 | For identical target words, compare synthesis with output register temporarily used as workspace vs not, including full reversal/cancellation of incoming unknown word z; don't count CX savings as scored | Valid arbitrary-z XOR and full phase/scratch; >0 real Toffoli gain against best valid control |
| C. Low-degree coded-word + sign gauge / table co-design | 10 wired banks show affine bit positions in all complete 16-row address blocks; gauge reparameterizations keep chemistry numerics but an earlier rewrite broke tens of thousands of code/tag constraints | Same physical Hamiltonian and verified integer words, impose RM/bit-tag constraints before changing entries, compile **all affected adjacent difference loaders**; identity control must reproduce k8<=211T or family<=3357T | Chemistry numerical error/lambda, complete KMB correctness for forward+reverse, cost below prior family |
| D. Invsqrt workspace Q37 -> Q36 | Official invsqrt cost Q*(T+Tgates/4), so Q improvement is potentially much more valuable than one loader T, but past arithmetic/phase changes failed | First audit precise lifetime, last-use/control/phase and recomputation costs, estimate T tradeoff. Only generate KMB if identified wire is provably reclaimable | Q=36, unchanged functional and phase error budget, actual Q*(T+Tgates/4) less than current 37Q file |

Evidence does **not** establish quantitative success probabilities. Rank by observed mechanism (A most specific), experimental discriminating power (B, C), and score leverage (D), without fabricating probabilistic expected values.

### Avoid two logical errors
- A's old->new difference is **correlation, not an attribution proof**; equal-compiler controlled experiments are needed.
- B's 3175 CX-with-output-controls is **structural difference, not proof that reading z saves T**. Compare real KMBs under identical contracts.
- C's numerical sign gauge is not free for the circuit; signed words can break the coded loading contract and reverse traversal.
- D's scoring advantage is conditional on a feasible width reduction and on no offsetting T/precision cost.

## Implementation and verification standard
For each track record: reference KMB/NPZ SHA, architecture distinctness/what new states or products become reachable, valid KMB path, T/HMR/CX/Q, forward+reverse and arbitrary-z input checks, all scratch0 and phase0, official Kickmix/Kaggle verifier if available, actual task-cost delta, failure reason. If zero first-stage evidence, kill or redesign that track rather than recycle seeds. Compare each track to the **best official verified score**, not to an obsolete 213/3375 baseline.

**Status: experiment definitions only; no improvement claimed by this document.** Prior GitHub sources: WHY_661_VS_211.md, WAVE_BROAD_15_REPORT.md, NEXT_NONLINEAR_CACHE.md and public Kaggle V8 (the source it rebuilds).
