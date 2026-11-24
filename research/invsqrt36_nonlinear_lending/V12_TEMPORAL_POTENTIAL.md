# V12: temporal nonlinear-state potentials and mixed Clifford words

Research only, NOT SUBMISSION. Base #57, reviewed #56/#58; #58 native donor receipts obtained from the peer archive. Main unchanged. No claim of worldwide novel mathematics or exhaustive audit of every historical branch.

## Verified results
|track|native ops|static paid|expected paid|source coverage|
|---|---:|---:|---:|---:|
|#57 cost|41333|1845|1675.3125|55567/60766|
|V12 cost|40743|1842|1673.4375|55567/60766|
|#57 wide|42294|1877|1696.3125|55829/60766|
|V12 wide|41868|1871|1692.9375|55829/60766|

Cost native SHA256 992f7aacd07839389537b22bf13c09cfea25f825911a6e55fd4da87a33a0c925; wide ea605794431d64a22de189087a6c637bf73650b19068dff106755a1798576eca. Direct independent BDD replay from pinned #57 parents: 39792/40984 comparisons, 250/199 exact changed spans, all 3133452 legal inputs, all 1173/1186 independent HMR events, equality of data, relative sign, rotation masks, classical bits and guards. Peak remains 37Q. No new 36Q coverage or official verifier/score.

## New structures
Multi-cut potentials: if U_t is the actual accumulated data map at a cut, form the vector space sum_t U_t^*(quadratic Boolean phase functions). Existing nonlinear data operations give extra cubic/higher-degree phase functions at no additional paid gate. Unlike #56 synthetic single boundary identity, search a full cut dictionary and emit native Z/CZ at legal times while preserving all data operations. Universal exact ANF: 12796/18000 columns, 73/96 windows, 0/3 selected cost/wide; wide saves 3 CCZ, 1.5 expected. Actual spans [18076,18105), [18895,18912), [32299,32318) of #57 wide. No new HMR, guard changes or chart crossing.

Reachable-state extension: 8192 sample rows, all 36 available physical wires, 41440/51428 phase columns, 15 sampled hits per track, 16/17 exact BDD tests, one accepted per track; 0.5 expected saved each. Exact domain and arbitrary independent HMR outcomes, not universal identities for reachable-only replacements. #58 phasebridge transfer: three native list matches per track, including exactly two identical repeated lists and identical replacements; missing moving tensor and dual donors not counted. Weighted phase subset cleanup removes 13/11 free operations.

Mixed Clifford words: exact action of X/CX/SWAP/Z/CZ on small affine-permutation + phase state, one stable classical guard per word. Forward BFS depth 4 on <=3 wires and 3 on 4 wires, reverse up to 3, windows <=9 operations. Actual 5708/5024 windows, 2408/1783 shorter words, 247/194 selected, -598/-442 ops. Universal exact ANF plus native roundtrip and whole paired BDD. Unlike prior affine-only MITM, phase and linear transformations are synthesized together; not full Clifford-group optimality.

## Negative width experiment
Remaining 94/91 gaps. Entire quadratic feature span on 35 retained wires in parked-swap or measured-output shapes: 22/59 eligible, no sampled decoder. Restricted sparse cubic atom modulo quadratic span, >=2 locally touched controls, 22/15 measured shapes, 4626/462 probes, no candidate. No new coverage; do not repeat this bounded family with just additional seeds. Does not exclude arbitrary cubic decoders, measurement-aware multi-cut coordinate paths, or other full36 designs.

## Lean and reproducibility
TemporalPotentialV12.lean contains three universal multi-cut native gate-list identities, three representative mixed-word identities, six resource lemmas, two generic potential identities and a conditional phase implication. Full reachable-state claims and final circuit replay are verified separately by BDD. No whole-oracle Lean proof. CI pinned Lean 4.35.0. v12_temporal_potential_core.py contains word solver and exact phase-span core; full runnable native scans, all receipts, source/parent KMBs, Lean generator and verifier are in GVQCC_V12_TemporalPotential_1842T_NOT_SUBMISSION.zip (SHA256 e5cd4c05be5e4fb0df129ffd76fbd3a906092e46a4773fc3edd0e2b85579dbcd). 

## Cost model (conditional, not official)
Use PR43 model, other task costs and overhead fixed: S0=33.1703164053, C0=60927.5479450, K=240.3779850. Cost Q37 31.54909589, hypothetical Q36 31.83855331; wide Q37 31.44266604, hypothetical Q36 31.73114699. Break-even Q36 E<1452.05390236, another >221.38359764 expected paid savings needed on cost branch. Do not mistake chart coverage or free command reduction for actual score increase.

## Additional references
- Bravyi/Maslov, Hadamard-Free Circuits Expose the Structure of the Clifford Group (2021), https://doi.org/10.1109/TIT.2021.3081415
- Maslov/Yang, CNOT circuits need little help to implement arbitrary Hadamard-free Clifford transformations they generate (2023), https://doi.org/10.1038/s41534-023-00760-2
- Bravyi/Shaydulin/Hu/Maslov, Clifford Circuit Optimization with Templates and Symbolic Pauli Gates (2021), https://doi.org/10.22331/q-2021-11-16-580
- Bravyi/Latone/Maslov, 6-qubit optimal Clifford circuits (2022), https://doi.org/10.1038/s41534-022-00583-7
- Fagan/Duncan, Optimising Clifford Circuits with Quantomatic (2019), https://doi.org/10.4204/EPTCS.287.5
- Hardware-tailored logical Clifford circuits for stabilizer codes (2026), https://doi.org/10.1038/s41534-026-01404-x
- Related earlier Amy/Lunderville, https://doi.org/10.1145/3704873; PhasePoly https://arxiv.org/abs/2506.20624.

Literature supports these directions; no external implementation benchmark or unique cumulative citation count asserted. Do not merge main. No submission.