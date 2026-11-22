# GVQCC — Claude Code handoff (2026-11-23)

Public GitHub draft PR: https://github.com/corcondor/gvqcc/pull/19
Public working branch: https://github.com/corcondor/gvqcc/tree/research/claude-handoff-global-angle-20261123

## Important: no official score update

None of the changed circuits in this bundle have been graded by the full official KickMix/Kaggle verifier. The C46 affine-gauge variant has 3,357 one-way ANGLE Toffolis with no reduction; the tested C45 joint variant has 4,429. Scores 33.13521306472748 and public 33.17023 are comparison targets, not records achieved by this bundle.

## Reproduce the hard evidence

Install Python 3.11+ and NumPy, then run from this directory:

```
python -m pip install numpy
python claude_recheck_bundle.py GVQCC_GLOBAL_ANGLE_20261123_SOURCE.zip --workdir reproduced
PYTHONPATH=reproduced/unpacked/src python gauge_constraint_full_audit.py --npz reproduced/unpacked/inputs/V8_C46_ORIGINAL.npz --out reproduced/gauge_constraint_full_audit_C46.json --expect-rank 70
```

Expected **LOCAL** results: I 1219 addresses x15 banks with 3357 Toffoli, Q128, zero phase/value errors, clean scratch; J 1237 addresses x15 banks with 4429 Toffoli, Q127, zero phase/value errors; 70 rank for 1219 addresses leaving 4 sign-frame variables per row.

All original research data (source files, 56 experimental KMB, angle-table NPZ, model physical data, negative experiments and SHA256_MANIFEST) is preserved *byte-for-byte* inside the 136-file nested ZIP.

## Development request (not satisfied yet)

1. Replace ANF-rank proxy with **actual compiled Toffoli plus width and physical-error feedback** in the joint 75-angle/FeMoCo/R/B/C/J search.
2. Use the full sign-frame nullspace of each address, but optimize globally across rows/banks. Keep original 3357T backend available by reversible affine conjugations when applicable.
3. Explore nonlocal multi-output XAG and cross-bank nonlinear intermediate products, not just one CCX fusion.
4. Independently evaluate the 37Q invsqrt schedule and 900Q DQI decoder for nonlocal width or arithmetic reduction.
5. Run *official* KickMix value, phase, work and physical tests on full 18-file output before calling a new score. Report SHA256s, measured T/Q, physical errors and exact scorecards.

The Zip's  136 files and verification passes are not evidence of a score update. Never claim they are.