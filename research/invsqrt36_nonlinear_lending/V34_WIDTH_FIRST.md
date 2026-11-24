# V34 width-first joint endpoint exchange and carrier compression

Research only, NOT SUBMISSION. Base PR83 native SHA256 8c3960d02d7c32dadbf307590ed7b8281bdd0aaabfa36dd86d95cce57bbabcb0. PR82/81 reviewed. No main or Kaggle mutation.

## Exact results
|track|ops|expected paid|static paid|full occupancy cuts|full occupancy runs|HMR symbols|
|---|---:|---:|---:|---:|---:|---:|
|V33|54127|22981/16|1588|5264|300|1286|
|V34 budget|54311|23221/16|1603|4576|281|1299|
|V34 wide|54415|23349/16|1611|4533|273|1307|

Budget SHA dab4064cf176e96db2c75d28fddb2f28336ff7125a43f99f91a460fe197d89b1; wide SHA 7b1ed0f528650121fd4b94055a33bb9a6308d056f71eefd58f3435b628a7ae75. Fresh serialized exact stream replay all 3,133,452 legal inputs, 54,094/54,110 paired checks, data/phase/rotation/classical/scope equal with extra independent HMR outcomes. All remain full 37Q. Prefix of wide (7495 native commands) physically allocated to 36Q and independently re-read and replayed: 7486 emitted ops, 414 static paid, 338 HMR variables, 2 rotations, 9 virtual swaps +10 zero exchanges; SHA 2c8623d49eae303564a4ac75bbd56e92f3460003c7956c8f181025ac1f8498b9. Open prefix only, not full oracle.

## Implemented structures
- 300 full runs all end at HMR. Initial [302,362) rank-one endpoint exchange and pre-generated zero-wire HMR result: 60 -> 35 body commands, 1->1 paid, 59 full cuts removed. One initial zero HMR added outside body. Sample 2 candidates, 1 accepted; second exact rejected. 211 rank(1,1), 27 rank(2,2) among supported simple windows; 234 data failures. Dense quadratic exchange 209 eligible, 2 data fits, both phase fail. No claim that generic rank-one exchange is sufficient.
- Whole degree-two polynomial kernel, projecting linear pivot and all incident quadratic coefficients, polar alternating-rank factorization. Pair-quotient atlas 8511 lenders,18 intervals/58 candidates; kernel 562 cuts,1579 relations,8 additional intervals/21 candidates.
- Untouched lifetimes across multiple barriers: 2367 lifetimes, top650 tested,2849 atlas cuts,1470 kernel cuts,22 candidates. Actual [31632,32391) q18=q8*q29 at both endpoints, q18 untouched, one extra paid gate replaces repeated restoration across 139 full cuts. Exact endpoint BDD certificates and per-gate projected replay.
- Complemented carrier mux: 457228 pair/complement probes,13 disjoint sample supports,3 affine separators at both endpoints,1 interval. Actual [12373,12706), A=q15, B=1 XOR q29, A*B=0, A=(A XOR B)*q0 at both endpoints. Encode t=A XOR B, measure A in X and compensate phase with m*t*q0; restore A and B via one CCX and CX. Both carriers untouched by source body. Three exact variants, one selected, 124 full cuts for +1 expected paid.
- 104 parked candidates with exact entry and exit certificates (including overlapping alternatives), plus 1 exact exchange, 49 distinct intervals. Weighted interval knapsack: 14 nonoverlapping chosen at +15 E, 688 cuts removed; 22 at +23 E,731 removed. Not 105 independent savings. Aborted long phase accumulator replaced by exact per-op streamed comparator. Direct full-phase audit attempted, resource failure; no alternate full oracle claimed.

## Literature and implementation scope
- Soeken/Tague/Dueck/Drechsler, Ancilla-free synthesis of large reversible functions using binary decision diagrams, doi:10.1016/j.jsc.2015.03.002: symbolic ancilla-free synthesis motivation; actual use of BDD endpoint acceptance and partial reachable projection, not Young subgroup algorithm.
- Patel/Markov/Hayes, https://arxiv.org/abs/quant-ph/0302002: linear reversible synthesis; current implementation uses existing row elimination/affine word optimizer, not their block algorithm.
- Meuli/Soeken/De Micheli, doi:10.1038/s41534-021-00514-y: XAG representation and space/paid trade-off; actual quadratic kernel and alternating rank factorization, not direct import of paper implementation.
- Yang/Yuan https://arxiv.org/abs/2611.02345 and Jeon/Huang/Cai https://arxiv.org/abs/2609.31605: deterministic measurement-based cleanup and phase debt; fresh zero HMR and mux phase correction. Prior citations, not claimed novel general MBU.
- Amy/Lunderville https://arxiv.org/abs/2410.23493: polynomial relation and phase folding; guard-specific sampled phase fitting and exact verification.

Fixed PR43 model: V33 37Q 32.97129, hypothetical36Q 33.27380. Budget 37Q 32.87355, hypothetical36Q 33.17516. Wide 37Q 32.82190, hypothetical36Q 33.12303. All hypothetical full36Q predictions, no official score increase; budget leaves only 0.7414 expected paid margin to original best. Need cost-neutral or negative further transformations. Complete36Q not achieved, no direct deletion from PR71's 80 products. Lean proves algebraic laws under explicit reachable premises, not full circuit. Historical ANGLE audit incomplete. Companion archive contains native files, scripts, all receipts and parent dependencies.
