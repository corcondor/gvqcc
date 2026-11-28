# V31: second-order Boolean selector quotient and rank-one repair
Research only, NOT SUBMISSION. V27 source SHA bd91d88909de18643262178477ca813c67dbcb2edc3325a99e66c964d6758258. Whole peak37Q. No official score change or global novelty claim.

## Exact results
44 V29 bridges, 169 single and 371 mixed deletion-selector columns; 146 mixed terms nonzero; 4671 bounded supports, zero newly zero second-order supports. Reproduced 54 V30 kernel supports, including all 53 failed affine data repairs. Two sample-data recoveries do not constitute independently verified improvements. 664 exact sampled trials, 89 rank-one eligible repairs, 63,213 raw products, 33 sample fits, 6 proposed bodies, 5 BDD PASS/1 phase reject. Sparse alternating-product screen 17,634,015 probes, 37 sample fits, same five accepted bodies. Four new reductions 13149:4→3, 35554:6.5→5, 36030:2→1, 43006:4→3. 33774:5→4 is a V30 duplicate (131→122 instructions relative to V30 local body). All legal inputs and symbolic histories. At 13149 both deleted q13*q15 updates equal new single evaluation on the full legal domain. At 36030 the two deleted products are not equal; quotient rank-one endpoint repair replaces them with one product. A proposed shortcut q9=h*q10 was explicitly refuted. Tail rank-10 phase obstruction reopened via 639,730 generated Z/CZ observation probes at 455 scope-free cuts, 13,644 signatures, zero direct/pair matches. This is a restricted negative result, not a lower bound against other synthesized observables.

| variant | expected paid | static paid | commands | V27 source coverage | groups | full cuts |
|---|---:|---:|---:|---:|---:|---:|
| V30 budget |1450.8125|1603|54068|45975|300|5281|
| V31 same-selection |1447.3125|1599|54105|45975|300|5281|
| V31 zero-budget |1406.3125|1551|54050|44618|319|6624|
| V31 width-priority |1451.8125|1605|54107|46075|298|5182|
All three exact serialized BDD PASS (3,133,452 inputs / 1,276 HMR variables). SHA256 respectively b4e944dd830cafbfb7bc877c91717b1ab1ed52dd5619b8edcd4ee35918d07085, c7c179797784f51654ff89172b1c0ad332327a31bf353ce4c91f7528a77847d5, 376d500f6c2ee49abf3bf3133e56dc9b352bbf3dc444db01132272f05653fe0b. Zero budget vs V28 zero: -13 commands, +100 coverage, -99 full cuts. Frozen Q36 hypothetical model 33.2013502877 at E1447.3125; remaining E budget <4.74140236. Current Q37 32.8995031231; zero budget Q37 33.1703164053. Full36Q not achieved.

## Mathematical and implementation notes
Mixed four-corner differences of the actual deletion selector semantics; Boolean idempotence s²=s produces additional terms compared to nilpotent jets. Linear adjoint retained for old-support comparison; second-order search computes forward sampled mixed differences, not a complete second-order backward solver. For retained affine function space W, product classes of elements of W define an alternating bilinear map W×W→F/W, since Boolean squares are linear. Compute raw pair product classes once and XOR them to evaluate sparse affine factor pairs. F/W is an additive quotient, not generally a ring. Candidate repair concentrates the rank-one unwanted direction into a pivot, injects one CCX, then applies affine repair. Guarded phase correction fits joint live-record dictionary. No truncation in BDD acceptance.

## Literature-use audit
- Higher-order derivatives: https://doi.org/10.1007/s10623-020-00738-7 and https://doi.org/10.1016/j.ins.2014.02.108 (mixed differences; adapted to gate selectors, not cryptanalytic attacks).
- Calik, Sonmez Turan, Peralta: https://doi.org/10.1007/s12095-020-00445-z (affine equivalence and multiplicative complexity; rank-one repair motivation, not classification algorithm).
- Reichl, Slivovsky, Szeider: https://doi.org/10.1609/aaai.v37i4.25524 and https://doi.org/10.4230/LIPIcs.SAT.2024.23 (contextual multi-output synthesis; our endpoint quotient + BDD, not QBF/SAT port).
- Bandyopadhyay et al.: https://doi.org/10.3390/quantum8040111 (reversible embedding and cost distinctions; preserve ABI, no DPLL port).
- Amy & Lunderville: https://doi.org/10.1145/3704873 (phase relations and nonlinear data).
- Morse: https://arxiv.org/abs/2608.30238 (related Boolean idempotence/exterior defects and Lean; abstract consulted, not implemented or independently checked).

## Reproduction and proof
Companion V31 ZIP in conversation, 174 files including V30 engine and original parents, scripts, KMBs, logs and SHA256 manifest. Run v31_joint.py, v31_wedge.py, v31_integrate.py, v31_budget_select.py, v31_exact_atoms.py, v31_relation.py, v31_tail_phase.py. Lean 4.35.0 certificate CI PASS https://github.com/corcondor/gvqcc/actions/runs/45492536980 at 0ceb60394ea8fd62d84ebca0dc13e5d7465063dd. General mixed product, guarded coefficients, wedge, rank-one, discrete coefficient adjoint; not full native Lean proof. Prior V30 corrected CI also PASS (run 45489638501). Historical ANGLE archive audit incomplete; peer PR78 official37Q is a different circuit parent, not integrated or additive. Main and Kaggle untouched.
