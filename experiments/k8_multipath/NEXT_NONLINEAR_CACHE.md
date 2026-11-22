# Next GVQCC experiment: stop score-neutral rewrites

Reference: public Kaggle V8 33.17023, 15 ANGLE loaders totaling 3357 T/pass. All source KMBs SHA-pinned in prior GitHub Actions run 45050045572. **No score update claimed.**

## New real-data check, 2026-11-23

Parsed all 15 KMBs, evaluated 1219 actual address rows with corresponding prior word bits, and computed GF(2) ranks of the 11 address signals, 35 initial word bits, constant, each scratch AND and each output AND.

| Banks | Scratch products | Output products | Output rank mod existing free+cache |
|---|---:|---:|---:|
| k0 | 147 | 98 | 98 |
| k1, k5, k7, k11 | 144 each | 96 each | 96 each |
| k2, k3, k4, k6, k9, k10, k12 | 82 each | 135 each | 135 each |
| k8, k13, k14 | 82 each | 129 each | 129 each |

Thus there is no redundant old output multiplication removable by just linear XOR feedback while all current cache functions remain. This **does not** establish global multiplicative complexity or exclude a new nonlinear cache/output basis.

For k8 the last eight cache products occur in 88-102 out of the 129 output-gate control expressions. These are high-impact structural choices: replacing them mandates resynthesis of the tail. Previously the old 213T vs public 211T diff changed exactly these last eight scratch products, with output count 131->129 and all output functions different.

## Concrete next compiler

Build `synthesize_tail(new_high_cache_products, target_words, max_qubits=128)`, which finds a new XOR–AND decomposition with GF2/matroid parity/FWHT and **writes a real KMB**. Baseline identity inputs must reproduce <=211T on k8; then test cache replacements **outside the original cache linear span**, not just free CX/negative-control/Fredkin equivalent rewrites. Verify all 1219 legal addresses, reverse traversal, phase and scratch, then official Kickmix. Scale to the other 14 banks only after passing k8.

Parallel higher-leverage alternatives: invsqrt 37->36Q with unchanged phase/error/T (hypothetical +0.304 score); DQI 900->899Q with unchanged average T and error rate (hypothetical +0.0246). In comparison 1 ANGLE T/pass saved across k8 implies only +0.00167 score if all else fixed. These are conditional arithmetic projections, not achieved improvements.

Reproducible 15-bank rank/cost mapping and the exact public KMB files are in the conversation artifact `GVQCC_NEXT_NONLINEAR_CACHE_RESEARCH_20261123.zip` with `cache_cost_map.py`, saved separately because GitHub tool only writes UTF-8 text. No Kaggle submission performed.
