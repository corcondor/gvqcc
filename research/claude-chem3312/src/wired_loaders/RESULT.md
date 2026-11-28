# w_push14 planner: 15 fewer chemistry loader Toffolis per pass (officially verified), 2026-11-26

Nothing was submitted, published or pushed. Official verifications ran on private Kaggle CPU kernels
(gvqcc-claude-v-plan-*), internet off.

## Result

**Final family `best/family_3341`: 3,341 loader Toffolis per pass (our current dc3356 has 3,356).**
Official dfthcsos verifier, unchanged, salts default and notebook-verification (78,016 shots each): PASS,
**cost 250,481,500.46** (current 251,051,553.94: -570,053.48), T 13,182, Q 405, lambda_eff 46.917982 (identical),
error_1/error_2 within 0.02. Local arithmetic with our b806 invsqrt (60,918.318) and the same DQI:
package score **33.17368 -> 33.19883 (+0.0251)**.

Candidate package (NOT submitted): `best/submission_chem3341_CANDIDATE_NOT_SUBMITTED.zip`
(sha256 2ef98b6c13838907529bc7e672189c75ae8fd1d271854d96012269e37adc284f): b806 with only dfthcsos members
replaced, every chemistry member byte-identical to the officially verified artifact, invsqrt and dqi unchanged.
Credits: `best/CREDITS_AND_NOTICE.md` (extends the b806 kit file; Syed Asad Ali first, then maoxin123;
goodpjw2008 for the method) and `best/family_3341/NOTICE.md`.
Receipts: `best/receipts/c3341_*.json` (kernel gvqcc-claude-v-plan-c3341).

| loader | before | now | what changed |
|---|---:|---:|---|
| 3 | 217 | 214 | rebuilt 39+42+47, 4 closers |
| 4 | 217 | 218 | rebuilt 39+45+47, 5 closers, no own free words (needed because bank 3 re-values batch 3) |
| 8 | 211 | 211 | rebuilt 39+39+47, 4 closers on donated words (needed because bank 9 re-values batch 8) |
| 9 | 217 | 214 | rebuilt 39+42+47, 4 closers |
| 10 | 217 | 214 | rebuilt 39+42+47, 4 closers |
| 12 | 217 | 214 | rebuilt 39+42+47, 4 closers, special columns (6,8) |
| 13 | 211 | 209 | rebuilt 39+42+42, 4 closers, special columns (6,9) |
| 14 | 210 | 208 | rebuilt 39+42+42, **3 closers**, special columns (6,9), own + donated words |
| 0,1,2,5,6,7,11 | | unchanged | byte-identical |

All 15 loaders: verify_one forward AND reverse PASS on all 1,219 addresses with HMR symbols.
Table: 1,127 words differ from dc3356, all physically dead cells (dead_mask_1e-13), batches 3, 8, 9, 12, 13, 14;
W, H2_I, H1_I, Hsym_lower, tree_edges identical; decoded vectors move by <= 3.4e-16.

Intermediate families, all official PASS at both salts: plan-b14-209 3,355 (251,013,550.38), plan-b1314 3,353
(250,937,543.25), plan-c121314 3,351 (250,861,536.12), plan-c3345 (250,633,514.72), plan-c3343 (250,557,507.59), plan-c3342
(250,519,504.03), plan-c3341 (final).

## Method (own planner; goodpjw2008's idea of paying zero columns with dead words)

1. Our loaders (maoxin123 lineage) are a three-stage triangular design (A 7 outputs/39, B 7/39, C 9-10/47-53, 4
   closers). The stage blocks carry no low-rank structure (no rank 1-3 element in R-perp) and are rigid under
   word edits, so a rebuild starts from scratch on top of the existing 82-product cache.
2. Block 1: 7 outputs, 13-dim low, 39 products. The engine solves unplanted targets in about 1 s.
3. Block 2: 8 outputs with one zero functional on the low space. Own-batch dead-word flips plus block-1 fan-outs
   pay it (one GF(2) system; the flips keep the cache-linear combos and the hyperplane constraint Phi of EVERY
   bank the cell enters). 42 products (engine, 10-60 s). Output subspace and functional are searched until the
   system is consistent; products are re-selected among all lines of the found subspace so block 3's functional
   stays payable (a product only helps block 3 with probability 3/4).
4. Block 3: the remaining 8 outputs (engine, 42) or 9 outputs (k8_ls gs2 + exact matroid-parity selection, 47),
   zero functional paid by block-1/2 fan-outs alone. gs2's greedy line count is only a lower bound: states are
   re-tested with the exact parity rank (this recovered solutions that had been discarded).
5. Special rows: `specgen.py` (parameterised rewrite of our pass-4 sp4lib/p4build): any two special columns > 2,
   any closer count, erasures from batch k or k-1, donor words absorbed by a neighbour's closers (that neighbour
   is then rebuilt with `--words ... --noerase`). Partition: `partition_row3.py` streams every 4th-level class and
   tests the remainder; luck up to about 90 bits in seconds to minutes.
6. Chains: a flip of batch k also changes loader k+1, which is therefore rebuilt after k. Segments used: 3-4,
   8-9-10, 12-13-14 (batches 4, 5, 6, 7, 10, 11 stay frozen).

Engines used as copies in planner/tmp: w_push14/engine `eng.exe`, k8_ls `gs2.exe`, pass-4 `cs2/cs3.exe`.

## Calibrated block sizes on unplanted targets from our table

| block | products | result |
|---|---:|---|
| 7 outputs, 13-dim | 39 / 38 | solved < 1 s / fails (7 lines) |
| 7 outputs, zero column | 38 | trivial |
| 8 outputs, zero column | 42 | solved (30 s; width 5000, weights 0,1,6,14,26) |
| 8 outputs, zero column | 41 | unplanted fails (29-30 lines); planted rank-1 solved 41/41; planted rank-2 36/41 |
| 8 outputs, 13-dim | 45 | gs2 solves (170-180 s) |
| 9 outputs, zero column | 47 | gs2 solves roughly 30-60% of attempts, 150-480 s each |

## Negative results (exact scope)
* Planted 41-product block 2 (bank 14 only): 20+ solved instances, but every one needed 6-13 products inside the
  kernel of block 3's functional (at most 5 allowed). Engine request: weight lines inside ker(z3) as zero.
* Bank 4 at 4 closers (95 bits of luck, all block weights 20): partition not found in 9 min; built with 5.
* Bank 12 on columns (7,14) at 4 closers needs 96 bits: not attempted; solved by redesign on columns (6,8).
* Bank 10 on columns (11,13) or (7,13): block-2 system inconsistent or unsolved (5 seeds).
* Not reachable with this design: banks 2 and 6 (too few free dead words for block 2); unwired 0,1,5,7,11.

## Files
design.py (blocks 1-3, dead-word system, selection), block3.py (parallel block-3 attempts), block2gs.py,
planted_design.py, planes.py (all lines, exact parity), specgen.py (special rows, build, verify, family),
partition_row3.py, verify_family.py, package.py; inst/ (instances + manifest.json), designs/, out/ (every built
loader and family), best/ (final family, receipts, candidate zip).
