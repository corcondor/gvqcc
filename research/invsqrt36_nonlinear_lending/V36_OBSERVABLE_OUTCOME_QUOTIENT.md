# V36 — observable-first symbolic transport and private outcome quotient

Research only. **NOT SUBMISSION. Whole circuit remains 37Q.** Stacked on PR86 for source history, but the actual native parent is the separately archived V35 PhaseLifetime DynamicRank combined candidate (SHA256 `4b7cfdd3d84ab8eff7494c45da3f583c7c476c571cc997e0fd3b9ca6d417abbc`), not PR86's other width/cost point.

- PR85 serialized parent, 3,809 full nonzero cuts (3,818 reported before physical relabeling): observable-first sampled screen 297 runs, 3,858 solves, 1,269 affine switches, 649 virtual writes; no cost-nonincreasing adoption. Independent serialized replay of unchanged parent PASS.
- On V35 combined parent: 59 same-reset runs, 19 exact symbolic transport bodies; budgeted selection of six with +15 static gate cap. Full-domain BDD proof of outcome independence succeeds in five, rejects one due to data dependence.
- Five accepted replacements at [7877,7888), [17025,17033), [17144,17152), [17313,17321), [30599,30614). Each has no q36 operands and local exact specialized data, phase, rotation, classical and guard checks PASS. All source data inputs 3,133,452; original 1,281 HMR variables. Source outcomes eliminated only after global derivative independence proof, not postselection. Internal transcript is **not** preserved; scope is the quantum oracle with private outcomes. The output is native serialized KMB, SHA256 `cf1ba95ab89d6c745f13a0629f8638afd0e3e62b8c8168b6bd9362d8dd130d2b`.
- Full nonzero cuts 3554 -> 3509; expected paid 22991/16 -> 23143/16 (+9.5); commands 51321 -> 51317. No claim of overall score gain or proof of 36Q.
- Deferred multi-expression ANF frame: 118 eager/lazy trials, 40 candidate bodies, including two newly expressible intervals [7520,7534) and [7686,7702), not accepted/verified globally. Exit failures 56, rotations 8, guards 14. No training or learned policy.
- Lean certificates verified via [Actions 45503123398](https://github.com/corcondor/gvqcc/actions/runs/45503123398): guarded observations, shared product, dirty-helper cubic construction, outcome specialization and parity derivative, carry identity. Generic Boolean lemmas, not formal proof of full native circuit or quantum measurement semantics.
- The result-saving script originally shadowed a file-path variable after serialized replay assertions; fixed, and a separate reread verifier is included in the companion archive. Parent raw byte hash recorded separately from normalized serialization.

## Literature checked
- Yang et al., Equality Saturation for Quantum Circuit Optimization, PLDI 2026, https://doi.org/10.1145/3808254. Bounded alternative selection motivation, not full Quasar implementation.
- SAT-Guided Conversion of Boolean Functions into Reversible Quantum Logic, 2026, https://www.mdpi.com/2624-960X/8/4/111. Partial reversible specification/care-set constraints; here direct symbolic ANF plus reachable BDD, not the paper's SAT solver.
- Amy and Stinchcombe, Polynomial-Time Classical Simulation of Hidden Shift Circuits via Confluent Rewriting of Symbolic Sums, Quantum 2025, https://doi.org/10.22331/q-2025-12-02-1926. Inspiration for symbolic phase cancellation only, not their hidden-shift algorithm.

Native exact edit bodies in v36_outcome_quotient_recipe.json; the full generators, source circuits, logs and BDD scripts are in the V36 companion archive. Preserve independent low-cost E1406.3125 baseline and width Pareto points. Main/Kaggle untouched.
