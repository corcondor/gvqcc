# V13: history-aware phase potentials and deferred scratch (NOT SUBMISSION)

Base #59 exact cost/wide native streams. Reviewed #56–58; #59 already contains admitted #58 phasebridge donors. No independent peer savings added arithmetically. #59 Lean CI succeeded (run 45382561913).

## Verified results
| candidate | native instructions | static paid | expected paid | source coverage |
|---|---:|---:|---:|---:|
| #59 cost | 40743 | 1842 | 1673.4375 | 55567/60766 |
| V13 cost | 40079 | 1833 | 1668.9375 | 55567/60766 |
| #59 wide | 41868 | 1871 | 1692.9375 | 55829/60766 |
| V13 wide economy | 41088 | 1860 | 1688.4375 | 55829/60766 |
| V13 deferred scratch (unfactored) | 41151 | 1896 | 1724.4375 | 55954/60766 |
| V13 deferred scratch (factored) | 41135 | 1876 | 1704.4375 | 55954/60766 |

Final KMB SHA256:
- cost 6ccc979036cd824e8a588615f6b9760ff95799574e202e4451a0b5ec211a426c
- wide economy 22a6fe003f4bf08c540201bba36b26ca92c5fa30b5ac2fec168a707d9b6d6189
- wide factored 7fdc624058fdb4e527728bb1d26f8c4608ffbcae7b7911055fd38a89397c7a3b

Fresh direct independent native-byte composition and full-domain BDD replay from #59: 39563/40936/40888 comparisons, 390/812/816 exact changed spans respectively, all 3133452 legal inputs and all 1173/1186/1186 independent HMR variables; zero events removed. Equality of basis data, phase, classical registers, active guards, rotation controls, and stack at all changed-span exits. Native angle/target sections unchanged. Peak still 37Q. Neither coverage nor free instructions is an official score gain.

## New architecture

1. Phase potential over the joint input/history function space. At every legal time cut, candidates are active_scope(t) * current classical guard(t) * q_i(t) or q_i(t)*q_j(t). Unlike #59 fixed guard/measurement-free blocks, allow transport across HMR, classical overwrites and nested scopes; no use of future guards at an earlier cut. Candidate dictionary with 4096 sample histories; one- or two-column matching, exact admission. Cost: 63 windows, 4406 distinct cuts, 1204295 columns, 13 sampled hits, 26 exact tests, 12 pass alternatives, 9 disjoint CCZ removals. Wide: 79/4151/1304074/14/23/15, 11 selected. Cost and wide expected saving 4.5 each. Actual [11023,11055) moves guarded CCZ(26,31,29) to guarded CZ(27,29) after HMR(27), CCX(26,31,27), preserving event 467 and rotation. New free columns not merely deletion of existing phase terms.
2. Exact instrument-null and guard-frame fold. Remove empty scopes, redundant classical writes, null quantum actions; remove provably tautological guard frames and conditions. Do not remove rotation parameters or HMR events. 667/782 operations removed after the history pass; no paid-cost change. Same entire classical memory and arbitrary HMR histories. Standard compiler ideas, not claimed mathematical novelty.
3. Dual of parked-payload decoding: if first SWAP parks old payload p on q36, hold p on original q_t instead. Omit writes to new scratch f; rewrite any supported data/phase reads using the other physical coordinates; after the original HMR resets a different q_u, SWAP(t,u) and materialize f on t. Do not fit a decoder for p. 91 residual wide gaps, 14 eligible shapes; whole quadratic span gives zero candidates. Sparse one/two cubic terms modulo quadratic span, restricted to at least two locally touched controls, 16185 cubic probes. 4/4 sample candidates accepted by full-domain BDD, source [22829,22859), [23357,23391), [24492,24524), [24953,24982), +125 covered original operations. Same HMR IDs/outcomes, no normalization/postselection. Initially each new decoder uses 10 CCX vs 1 original; all four use two cubic monomials sharing two factors. Factor them as a three-dimensional affine subspace, enumerate 168 ordered GL(3,2) bases x 8 complement choices = 1344 each, 5376 total. Factor the cubic jointly with quadratic residual; exact universal ANF re-synthesis 10 -> 5 CCX per decoder, -20 static/expected and -16 instructions from unfactored candidate. Final width extension costs +16 expected vs V13 wide economy; not an economically superior replacement.

Example source [22829,22859), t=26,u=23. After original HMR(23), retain old p via SWAP(26,23); decoder for q26 in post-reset coordinates is
f = q32(q7 xor q29) xor q7 xor q32 xor q17(1 xor q32)(1 xor q7 xor q12).
It uses one quadratic factor and a factored cubic, with four-CCX dirty borrowed-wire implementation of the cubic. Exact all-state ANF for optimized decoder, reachable condition separately proved by full BDD replay. No claim of minimum cost or unprecedented mathematics.

## Lean
HistoryScratchV13.lean: four actual universal decoder-list equivalences and resource theorems, actual history span with unchanged nested IF flattened to same guarded CZs, actual deferred gap under explicit reachable decoder/entry zero premise, and generic delayed scratch/dirty cubic/guard partition laws. CI pinned Lean 4.35.0. Whole KMB, exact reachability and instrument verification remain independent BDD checks. Core cubic synth in v13_cubic_hub_core.py; runnable compiler, all native files, receipts and exact replay in companion ZIP. Do not merge main.

## Conditional score
PR43 model only: S0=33.1703164053, C0=60927.54794503887, K=240.37798500105055. Cost E=1668.9375 predicts Q37 31.57386211; hypothetical Q36 31.86354675. Wide economy E=1688.4375: Q37 31.46709937 / Q36 31.75580448. Expanded wide E=1704.4375: Q37 31.38056834 / Q36 31.66847955. Need E<1452.05390236114 at full36Q, another >216.88359764 expected paid reduction on cost. No official verifier/score/submission.

## Related literature
- Fulginiti et al., Compile-Time Simplification of Classically Controlled Operations in Dynamic Circuits (2026), https://arxiv.org/abs/2605.28439
- Dead gate elimination in hybrid quantum-classical programs (2026), https://doi.org/10.1016/j.jocs.2026.102789
- Liu, Zhou, Meng, Quantum Uncomputation of Clean and Dirty Ancilla Qubits (2026), https://arxiv.org/abs/2608.09578
- Quantum circuits with classical channels and the principle of deferred measurements (2022), https://doi.org/10.1016/j.tcs.2022.02.002
- The T-Complexity Costs of Error Correction for Control Flow in Quantum Computation (2024), https://doi.org/10.1145/3656397
- Amy/Lunderville, Linear and Non-linear Relational Analyses for Quantum Program Optimization (2025), https://doi.org/10.1145/3704873 (previous reference; closest mathematical connection)
These support classical-quantum relational analysis, control flow semantics, ancilla reclamation, and exact verification. Not claims of reproducing external optimizers, nor exhaustive world novelty or unique cumulative citation count.
