# V83 — ANGLE 3300 target: exact reachable-state audit (not a submission)

Status: **NO ACCEPTED PAID-GATE REDUCTION. No claim of <3300 or score improvement.**

## Provenance
- Exact source programs for k=1..14: [Acceleratorer exp-074](https://github.com/Acceleratorer/quantum-circuit-compilation-clean/tree/main/experiments/exp-074), module/payload/v20_loader_programs.b85 and module/build_chemistry.py, derived from goodpjw2008's public work. Attribution retained; consult upstream NOTICE.md and LICENSE. The public exp-074 receipt counts 3325 Toffolis/pass, including its k0=263.
- Older legal-angle fixture: [gvqcc PR20](https://github.com/corcondor/gvqcc/pull/20), experiments/oss_chained_angle/v8_c46_angle_fixture_public.json on experiment/oss-chained-xag-20261123.
- Latest public notebook archive [Alex Chilton 33.25](https://github.com/corcondor/gvqcc/tree/main/references/kaggle/alexchilton) reports chemistry 95f5de29, 3306 Toffolis/pass, 405Q, T=13112. Actual 3306 KMB/NPZ not available in this execution; the archived notebook is not a circuit binary.
- The recreated 14 V20 programs have 3062 CCX, matching the exp-074 per-bank count. The old fixture differs on active rows for k13 and k14; it cannot be substituted for V20's exact complete submission table.

## Executed experiments
| k | CCX | HMR | Active-row mismatch vs old fixture |
|---|---:|---:|---:|
| 1 | 240 | 144 | 0 |
| 2 | 214 | 82 | 0 |
| 3 | 212 | 82 | 0 |
| 4 | 213 | 82 | 0 |
| 5 | 240 | 144 | 0 |
| 6 | 213 | 82 | 0 |
| 7 | 240 | 144 | 0 |
| 8 | 205 | 82 | 0 |
| 9 | 212 | 82 | 0 |
| 10 | 212 | 82 | 0 |
| 11 | 240 | 144 | 0 |
| 12 | 209 | 82 | 0 |
| 13 | 206 | 82 | 53 |
| 14 | 206 | 82 | 100 |
All fourteen generated instruction sequences replayed on all 1219 address rows, forward/reverse, including scratch restoration and per-HMR phase polynomial constant across addresses (global phase allowed). This is a source-level packed simulator, not KickMix official verification.

- Simultaneous forward/reverse affine gate substitution: all 3062 CCX examined, zero replacements.
- Cross-bank propagation of angle changes, with window programs held fixed: zero attainable nonzero dead-angle changes in the span of existing regular-bank linear/product features at every stage, all five slots, using the reconstructed words and tree. Not a universal lower bound.
- Window CP rank-one factors: 192 independent low/output vectors, high-factor rank 151; candidate paired planes in the same span 101,100,100,98 for k1,5,7,11. No physically synthesized improvement.
- Mixed-column feature compression: enumerate all 256 mix patterns for each high row under existing output factors and free high coefficients; no single affine dependence among the four bits of either special column feasible on all 76 full rows, in any of ten regular banks. Restricted search, not a universal lower bound.
- Special-only output-term descent (k2,8,14) rejected.

## Reproduce
```sh
node research/v83/run.cjs /path/to/v8_c46_angle_fixture_public.json /path/to/v20_loader_programs.b85
```
The core and runner use no external JS packages. The runner reproduces the executed audit classes, not an official verifier. The source program provenance is explicitly separate from the missing 3306 parent. No change to main and no competition submission made.
