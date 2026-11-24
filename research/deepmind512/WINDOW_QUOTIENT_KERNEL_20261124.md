# 2026-11-24 — 128-wire window quotient and bilinear kernel search

Status: **NO GAIN**, no candidate to submit. Fixed public V8 input archive SHA256 0211ca05bc492b1312dce58a6978a2a527ff25e978e3f1b986c280b50d4f27f2, 15 native ANGLE banks, 3357 CCX / 128Q, k8/k13/k14 each 211. Angle table unchanged.

This is distinct from PR #21's at-most-six-wire micro-rewrites and PR #22's one-CCX affine scan / cross-bank affine frames. PR #22 head 4ef14605144f2f45ac959fabc42a3014d9f132ca had three successful CI jobs, but that does not certify this new experiment.

## Formal specification
For a measurement-free X/CX/CCX window, let S and E be spans of the 128 wire truth masks on 2438 legal forward/backward inputs, with constant 1. Every CCX adds at most one new direction to the cumulative span; any such replacement must use at least dim(S+E)-dim(S) CCX. This is a necessary bound, not synthesis. If aiming for the bound by monotone subspace transitions, at current S choose a,b in S with p=a*b in S+E outside S. Write p=s+e, s in S, e in E; require s independent of (S intersect E) plus a,b, so the affine frame can use s as a distinct target and retain the intersection and controls. Then target becomes e, increasing overlap by one at fixed width.

## Actual results (local Python, original native KMB parsed)
- All 15 baseline banks, 1219 addresses x two directions, address/word/scratch/phase errors zero; 1543 HMR outcome coefficients checked symbolically, no conditional data gates. Not official KickMix.
- All 660 post-first-HMR CCX (previous audit excluded them): single affine replacement 0.
- 19,834 windows, 2..8 consecutive paid gates with no intervening HMR or conditional phase. 330 windows with lower bound smaller than original cost: 4->3:5; 5->4:19; 6->5:48; 7->6:91; 7->5:2; 8->7:145; 8->6:20. All 3028 two-gate windows have lower bound two.
- All 330: original products sequentially independent relative to cumulative input span; no proper subsequence of original products suffices to generate E even with unbounded retention of signals.
- Five 4->3 lower-bound windows: k6 [23567,24151], k12 [24341,24969], k13 [20530,21127], k13 [22742,23361], k14 [19181,19819] (inclusive native op indices, zero based). Search original control-factor span: 561353 product evaluations, 0 complete plans. Expanded search: fix a from original factors/current wires and solve a*b in S+E via exact GF2 linear kernel over all live wires; enumerate kernel basis and pairwise sums. 1,891,316 product evaluations (including repeated candidates), two admissible one-step transitions (k6/k12), zero 3-step plans.
- Regression: 4 bank roundtrips; removal of one CCX or one conditional CZ in each of those banks caught by independent verifier (8 negatives); rank unit test passed.
- No complete new plan, hence no candidate-specific Lean proof, no new native KMB, no official score. Not a proof of optimality; the factor pool, kernel combinations, choice of frame, monotone overlap and beam caps limit search. The next iteration should not repeat this exact scan.

## Reproducibility record
Local source/results archive GVQCC_window_quotient_kernel_audit_20261124_NO_GAIN.zip, SHA256 ccddb4f6f3fba0f716f36a075c39080b5a0e74585977e10077d1029b37d4097f. Contains Python scripts scan.py, window_scan.py, long_window.py, analyze_candidates.py, merge_search.py, kernel_search.py, test_audit.py, native KMB parser and GF2 support, JSON results and per-file manifest. Run sequentially with the fixed original ZIP and NumPy: python scan.py ZIP; python window_scan.py ZIP; python long_window.py ZIP 8; python analyze_candidates.py ZIP; python merge_search.py ZIP; python kernel_search.py ZIP; python test_audit.py ZIP.
No main changes, no Kaggle submission, no score claimed. Future targets: nonmonotone frame exploration and HMR-aware phase-space synthesis, or different nonlinear factorizations beyond these pools. The 349T merged pair is still non-callable.
