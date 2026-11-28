# V78: adaptive quotient synthesis (research; not a submission)

Acceptance is still Issue #163. The latest independent 24Q invsqrt candidate is a single complete KMB, not an assembly of partial-circuit minima.

| Circuit | Q | CCX | generic rotations | ops | formula cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| V77 matched parent | 24 | 4647 | 7777 | 59874 | 1619179.6695805548 |
| sparse-refit | 24 | 4432 | 7689 | 58525 | 1596535.808390842 |
| refit + reciprocal-representative exchange | 24 | 4416 | 7681 | 58449 | 1594562.6077187853 |

Final SHA256: 0894af85f1b2176e9fe37802abaca56fae80b4fdf66f03d394d6c483c3f5a269.
Independent native replay: all 4194304 basis inputs, 3133452 legal inputs, 1982 independent HMR coefficients; exact 128-bit phase contraction and restoration PASS. Minimum integer margin 138112178 unchanged. Neither official verifier nor competition score. Noncompetitive versus historical cost 60927.56. At Q=24 and that margin, 31 generic rotations leave at most 2322 CCX for beating that historical cost. Even zero rotations leave only 2538 CCX.

Algorithm: signed Walsh coset columns are removed/refitted with a Chebyshev LP and full-domain counterexample cuts. Candidate new supports are priced from the residual Fourier transform; 6876 -> 6780 cosets. An exact integer reciprocal support MILP and signed representative cancellation further reduce the native circuit. Lattice refit alone and rank-2 regrouping alone were rejected on the native formula cost. See companion ZIP for actual source, plans, circuits and receipts. The set-cover MILP optimum is for its finite candidate family only.

DQI: two exact classical full-size models, 52 tests each. Root-free blocked Horner with evaluation/interpolation and characteristic-two reciprocal lift reduces maximum counted variable field products in the remainder core 143325 -> 23781. Then compute magnitude interpolant in GF(4096)[X]/P by inverting the square root of P' modulo P, squaring and multiplying by the syndrome numerator. The resulting scan needs only fixed linear field evaluations and zero testing at each of 4095 positions. Maximum 1860 variable field products + 20 field inversions in the interpolant core, excluding BM, scan, reversible scheduling and uncomputation. All 52 phase answers agree with direct sparse error masks. No new physical DQI KMB or competition cost claim.

Chemistry: coupled physical-metric Grassmann projection C46->45 preserving H1 and gap before refit. Full numerical e2 20.83713749 mHa, then 1645 evaluations of weight refit yielded 20.55037689 mHa (e1=20.01581757); rejected. The C46 exact Jacobi gauge search of W/H2 gives only 1.9e-10 Lambda decrease, comparable to numerical resolution; no substantive gain. 15 ANGLE banks unchanged. No claim of CCX/Q or score improvement.

References: Amy & Lunderville, POPL 2025, DOI 10.1145/3704873 (nonlinear relational analysis; independently implemented residual-driven basis exchange); Bostan & Mori, SOSA 2021, arXiv:2008.08822 (polynomial recurrence/reciprocal viewpoint; not a direct reimplementation of their single-term algorithm); Gao & Mateer 2010 (finite-field evaluation interpolation); Halpenny, Sireesh & Wallden, arXiv:2611.26605 (Nov 19 2026; in-place arithmetic/error transport; QFT-based algorithm not ported to KMB). V77's conditional-clean ladder (Khattar/Gidney, DOI 10.22331/q-2025-05-21-1752) is reused. Review PRs #20, #148, #155, #157–#167. No claims that all PRs were read in full.

Lean local algebra only; no whole circuit formal semantics. No main changes or Kaggle submission. All research artifacts are NOT SUBMISSION.
