# V54 — 22Q-first phase synthesis, balanced embedding and complement transport

**Research diagnostics only. NOT SUBMISSION.** Do not confuse analytic target approximation with exact source-oracle equivalence. No official verifier, no score claim, no main merge, no Kaggle modification.

## Parent and coordination
PR119 is the 22Q comparison parent (55,606 CCX, 15,287 rotations, 115,245 ops). PR92 is the exact but dense 22Q existence witness. PR121's 23Q low-rotation construction, PR120/122's 37Q/32-rotation repair, and PR112's trilinear factors are distinct tracks, not additive reductions. The target is a competitive 22Q oracle with no extra qubit, not a 37Q patch.

## Native whole-oracle experiments
New dyadic spectral plans generated from the analytic target with exact legal tolerance checks. Prefix constants and spectra are expanded as signed parity terms; affine translation directions jointly cover multiple suffix parities; all their unconditional compensations are aggregated. Compare unit-vector directions with affine directions and vary the maximum prefix depth. The independently reread and contracted circuits below restore all 22 inputs and have no HMR. Exact modular phase contraction agrees with each candidate's plan on all 4,194,304 inputs. Integer squared tolerance passes on 3,133,452 legal inputs; worst analytic error ratio 0.7794987466186285. Not official or competitive; arbitrary rotation costs dominate.

| Candidate | Native ops | CCX | Generic rotations |
|---|---:|---:|---:|
| PR119 reference |115245|55606|15287|
| plan_0_affine_16 |78299|31406|14827|
| plan_0_affine_14 |69062|24062|14938|
| plan_3_affine_12 |56058|11694|16510|
| plan_10_affine_12 |56291|8518|17627|
| plan_10_affine_16 |62199|13910|17047|

SHA256 plan_0_affine_16 ae13cef3429eeadb6aa19f4e8b09fd9566794b633624c2eff10f5ed3d885a27f; plan_0_affine_14 4c38a1e8d906364dcc3fb0784531814e57be60e9312018aa424b1aec81934751; plan_3_affine_12 b7968805d43f57fdb5b8d1aacc98c312931414df47b92ca096183610f5eea0ed; plan_10_affine_12 281bcab6f3603ed4ce781c540d65eae624476f5895ce1bef3d41d8ce644ba16c.

## Constructive low-rotation route, NOT full native circuit
For S=2^34, choose A(x)=round(S/sqrt(x)) mod S by integer square-root comparisons. Verify exact squared inequality with relative tolerance 2^-24 for every legal x; maximum approximate reporting ratio 0.8637432046234608. Use the 1,060,852 illegal inputs to balance each phase predicate. Dense predicates split in two; sparse predicates use the difference of two balanced controls. All ten negative observations coincide with the original pivot q21; collect their angles modulo one turn. 45 observations before merging -> 36 total rotations (33 generic, three grid rotations). Full-domain balanced mask and even-permutation coordinate replay, legal phase-word equality, and exact tolerance PASS. Pairwise even-permutation implementation is constructive, but requires 18,944,216 transpositions before the inverse pass. DO NOT claim native 33-rotation 22Q oracle, competitive cost, or official verifier PASS.

## Native upper four phase bits, NOT whole oracle
Replace arbitrary paired swaps with the complement-pair gauge x -> 2^22-1-x on sparse supports. Fanout from q21 into the lower 21 wires makes complementary input pairs share their lower-coordinate labels. Choose the illegal pair at x=0 to make the toggle predicate even. Synthesize the predicate as XOR of dyadic cubes; convert paired singleton endpoints into a path of 2-point cubes, no ancilla. Jointly choose a tour through the four predicates; transition uses their symmetric difference, keeping the common frame across stages. The 34-bit plan's bits 30..33:
- Arbitrary even-permutation fragment 66,617 ops /38,248 CCX/5 rotations.
- Complement frame fragment 10,287 ops/8,016 CCX/5 rotations, including one shared negative rotation; independent compute/uncompute cube costs 13,004 vs 10,240 shared tour costs. Serialized full-cube control-mask and input-restoration checks PASS. SHA c43ae37aac56db9ba24ce4dc6c9aedfef63b8c50ae0964e72572f7a395fe6ba1.
- Neither fragment implements the lower 30 bits or the entire inverse square root. The main unresolved task is compressing low phase predicates into economical simultaneous reversible permutations, rather than individually balancing dense truth tables.

## Theory and sources
Walsh expansion and phase-parity synthesis: Welch et al., Efficient quantum circuits for diagonal unitaries without ancillas (2014), https://doi.org/10.1088/1367-2630/16/3/033040 . Relative phase / phase-state duality: Amy and Ross, https://doi.org/10.1103/PhysRevA.104.052602 . Conditionally clean ancillae: Khattar and Gidney, https://arxiv.org/abs/2407.17966 . OpenAI/math Family379 finite Fourier and matrix multiplication: relevant inspiration for shared factorizations, NOT an asymptotic theorem implementation or a physical gate bound. This new branch uses finite bitwise parity transport and exact integer arithmetic. 
Lean certificates cover finite local identities, padding/cardinality cases and complement bounds, not the whole quantum circuit, permutation compiler or score. Reproduction archive includes complete native emitter/verification scripts, phase plans, KMBs and receipts. No training.
