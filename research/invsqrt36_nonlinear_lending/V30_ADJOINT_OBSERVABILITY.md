# V30 — backward adjoint observability and exact phase quotient
Research only, NOT SUBMISSION. Parent PR77; original V27 source SHA bd91d88909de18643262178477ca813c67dbcb2edc3325a99e66c964d6758258. No main/Kaggle changes. Full 36Q or official score improvement not achieved.

## Implemented algorithms and exact results
- Phase-aware observability don't-care: perturb one target, propagate its exact Boolean difference, include every final data bit, cumulative sign and individual rotation in the care mask, and try affine resubstitution only on observable assignments. 162 bridge paid CCX pullbacks, 3 partial care masks, 0 fits. This is a negative screen, not a lower bound.
- Backward transpose-Jacobian over sampled reachable assignments: lanes for data, sign, individual rotation control. At CCX, pull back target sensitivity to controls with the other control as coefficient. At HMR, multiply retained target sensitivity by NOT guard and add the measurement-outcome times guard sign coefficient. Project data lanes modulo the span of endpoint coordinates and phase lane modulo free observed phases plus endpoint affine functions. Find nullspace groups, then replay with exact nonlinear interaction terms. This linearized search is a heuristic, not a Boolean chain-rule equivalence proof.
- 44 V29 bridges: 169 paid columns, kernel dimensions summed 49, 54 trials, 53 fail nonlinear data repair, one exact accepted. [33774,33902): 5→4 expected/static paid, 130→131 local commands; same 36Q boundary ABI. V28 originally cost 11.5.
- Whole V29 fixed-compact source: 651 windows, 9756 adjoint columns, max depth 66 paid columns, 508 windows with nontrivial kernel, 1007 joint trials (up to 15 deletions), 83 sampled passes, 6 best window proposals. Exact BDD accepts one; five tail proposals match data/rotation/classical/guard but fail phase.
- Accepted native [231,397): omit CCX(19,21,15) at original index319; reachable-state endpoint quotient gives 182-instruction affine repair, reduced by exact affine-map resynthesis to 18. Native region 166→151 commands, 9→8 paid, q36 identically zero throughout both region trajectories. Serialized full paired replay: all 3,133,452 legal inputs and 1,276 independent HMR variables, phase ledger, data, classical, rotations, guards and cost PASS.
- Exact phase obstruction [48546,50362): expand BDD observations into sparse ANF over independent HMR variables with exact packed legal-input truth tables as coefficients. 967 observations, 957 free, 10 paid; free rank951, joint rank961, all ten paid independent modulo available free phase observations. 1843 ANF terms in total, max20 per observation, no cap skips. Therefore no nonempty paid subset can be removed by XOR of only those existing free observations, on unchanged trajectory. Not a bound on generated observations or changed nonlinear data.
- Whole V30 fixed compact: SHA256 56d5f65b78d40dac0bca72602d08248b0690307debe2037e2a2ee56af76d0f61, 54,094 commands (−15), 1597 static paid (−1), E=23101/16=1443.8125 (−1), 5567 full cuts unchanged. Compared with V29 fixed compact e668599e… .
- Separate V30 budget compact integrates the [33774,33902) bridge on the exact original V27 chart ABI: SHA256 806164878a471e23fd44cf2d61384be685796ab9501fc511b085d8127757d64c, 54,068 commands (−4), 1603 static paid (−1), E=23213/16=1450.8125 (−1), 45,975/53,416 source coverage, 300 groups, 5281 full cuts unchanged. Fresh paired serialized BDD PASS. Do not add savings across these distinct parents without replay.
- Whole peak remains37Q. Original low-cost E=1406.3125 not beaten. Four older ANGLE archives remain unavailable.

## Literature-use audit
Mishchenko & Brayton (2007), SAT-Based Complete Don't-Care Computation, https://arxiv.org/abs/0710.4695 — windowed observability/resubstitution concept implemented using bit-packed simulations and exact BDD acceptance instead of their SAT algorithm.
Reichl, Slivovsky & Szeider (2024), eSLIM, https://doi.org/10.4230/LIPIcs.SAT.2024.23 — multi-output Boolean-relation/window formulation; here the endpoint quotient includes output data, sign and rotation, not their SAT/QBF solver.
Mishchenko et al. (2024), Standardizing Boolean Transforms, https://people.eecs.berkeley.edu/~alanmi/publications/2024/tech24_resub.pdf — simulation signatures, side divisors and multi-output transforms; implemented signature quotient and exact verification, not ABC port.
Marakkalage et al. (TCAD 2026), Scalable Sequential Logic Synthesis Using Observability Don't Care Conditions, https://doi.org/10.1109/TCAD.2025.3583206 — reachable-state observability motivates care mask; no k-induction algorithm port.
Amy & Lunderville (2025), https://doi.org/10.1145/3704873 — relational phase folding; here sparse HMR coefficient ANF and exact row rank, rather than their polynomial abstract interpreter.
Prior V29 discrete GF2 summation by parts extended to a transpose-Jacobian step with exact quadratic remainder; Lean source includes local CCX/HMR identities and concrete 182→18 affine word row equality. Full reachability still BDD, not Lean.

## Reproduction
Full companion conversation ZIP contains engine and exact parents, scripts and candidate/receipt files:
```
python v30_observable.py
python v30_adjoint.py
python v30_adjoint.py v29_fixed_compact_NOT_SUBMISSION.kmb 1536
python v30_verify.py v29_fixed_compact_NOT_SUBMISSION.kmb v30_native_candidates.pkl v30_native_fixed_NOT_SUBMISSION.kmb
python v30_verify.py v29_fixed_compact_NOT_SUBMISSION.kmb v30_compact_candidates.pkl v30_native_compact_NOT_SUBMISSION.kmb
python v30_phase_quotient.py v29_fixed_compact_NOT_SUBMISSION.kmb 48546 50362 v30_phase_quotient.json
python v30_integrate.py v30_budget_compact_NOT_SUBMISSION.kmb
```
No official score claim or global novelty claim.
