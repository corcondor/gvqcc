# V6 joint multi-wire delta synthesis — diagnostic, NOT submission

Parent: PR #36 (ff420015f0f1b7dfaa56ed2e5d56bba22298b652), full KMB SHA256 b1978632f8e7df632406099a7d0a7f2b0ec133df4b973439998226a8c8ff0c9f. Discovery reference PR #31 V5 wide d7e14b3cc42cebd9fc8df5047fc9f21978981f80841b34b5ea980c4f8fe4989d. Original source 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03. Recovered both V5 archives and PR36 V6 archive. PR35 reports 89.3526% at 1895 paid; its executable archive was not obtained in this turn, so no splice into it or additive coverage claim. PR34 literature/pattern track noted.

## Method and actual experiment
For connected sets of 2 or 3 target wires, find epochs with closed outward dependencies and internal target interactions. Independent erase/reconstruct variant: 8,435 connected target sets, 234 complete epochs, 468 endpoint fits, no sampled positive. Different from PR32 single write-only target: keep old target data as joint latent coordinate. Drop all target writes in epoch, independently run external instructions, then solve A_out y = A_in x XOR p(z_out) with distinct invertible input/output GF(2) bases. For each input/output parity pair fit quadratic increments in external final state, factor and emit actual CCX. Dynamic programming over both independent spans (weighted common-basis problem); verify full gate program, not rank alone.
987 complete/subepochs, 4,426 feasible parity pairs, 29 feasible frames, 27 sample-positive, 14 exact local BDD positive, 13 rejected. Restrict same algorithm to those classes; do not repeat unchanged merely with new seeds. Select disjoint actual regions by sequence match, paid and instruction count. One candidate is already changed by PR32's lifetime donor and is excluded on PR36 (no double counting). Three selected disjoint complete source slices on PR36:
- [8110,8143): CCX 3 -> 2, input q35=0.
- [8158,8170): CCX 10 -> 2, exact input residual condition in JointDeltaV6.lean.
- [42323,42335): CCX 5 -> 3, unconditional Boolean equivalence.
All changed slices use only q0..q35; no HMR or phase/rotation operations changed. Complete native binary roundtrip, 62,823 paired composition checks PASS on all 3,133,452 legal x and 1,168 independent parent HMR variables. Static paid 1904 -> 1893; expected 1721.8125 -> 1710.8125. Candidate SHA256 2a59cb3511da8d6ea1f6ae6b87e916eee10a1f5652ba3ddd354afc77b61406b2. Parent chart coverage 53749/60766 (88.4524%); no new coverage claimed. Whole width still 37Q. No official KickMix, score update, or submission. No claim of beating original 37Q expected paid 1406.3125. No claim of complete historical ANGLE source audit or cold-start 50% allocation.

## Lean
Actual gate lists, width and cost proofs in lean/JointDeltaV6.lean; two lemmas conditional on independently established reachability and one universal. CI separately executes Lean 4.35.0. This is not a full-oracle Lean proof. The research archive contains the actual source/parent KMB, generated candidate, executable search and all comparison receipts; run v6_joint_epochs.py, v6_delta_epochs.py and v6_apply_joint.py in central/global_chart with supplied pinned inputs. Pickles only from trusted research files.

## Additional sources and technical connection
- Boyar & Find, Multiplicative Complexity of Vector Valued Boolean Functions, TCS 720 (2018), https://doi.org/10.1016/j.tcs.2018.02.023 and https://arxiv.org/abs/1407.6169 — vector-valued AND count rather than individual output minimization.
- Lawler, Matroid Intersection Algorithms, https://www2.eecs.berkeley.edu/Pubs/TechRpts/1971/Archive/ERL-m-333.pdf — selecting row pairs independent in both input/output linear matroids; our small-frame exact DP uses this common-basis formulation, not a claim of implementing Lawler's algorithm.
- Patel, Markov, Hayes, Optimal Synthesis of Linear Reversible Circuits, https://arxiv.org/abs/quant-ph/0302002 — reversible affine frame realization; current code uses Gaussian elimination.
- Calik, Turan, Peralta, The Multiplicative Complexity of 6-variable Boolean Functions, https://doi.org/10.1007/s12095-018-0297-2 — affine equivalence and bounded exact synthesis for further joint decoder research.
- Boyar, Peralta, Pochuev, On the multiplicative complexity of Boolean functions over the basis (AND,XOR,1), https://doi.org/10.1016/S0304-3975(99)00182-6 — cost metric and constructive AND minimization.
- Amy & Lunderville, https://arxiv.org/abs/2410.23493 — nonlinear reachable relations, prior V5 reference.
- Yang et al., Quasar, Equality Saturation for Quantum Circuit Optimization, https://doi.org/10.1145/3808254 — maintain multiple equivalent representations; not executed here.
- DeepMind formal quantum computation and Ichikawa et al. https://arxiv.org/abs/2503.09356 retained from parents. No QAOA or external compiler benchmark claim for this new run.

## Handoff
PR35/36/34 owners: use actual sequence matching plus exact all-history full composition; do not count overlapping lifetime savings or source coverage blindly. Next distinct operator: enlarge the *joint* reversible frame via weighted common basis with independently measured nonlinear transitions and guarded branch-specific latent coordinates. Avoid single-wire erase and same closed-epoch DP retries. No main changes or merge.
