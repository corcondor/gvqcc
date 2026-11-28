# GVQCC: physically invariant global patterns K / O and nonlocal B/R combination — 2026-11-23

**Important: NO officially verified overall-score improvement.** Targets remain 33.13521306472748 and publicly reported 33.17023. The tests below do **not** constitute an official KickMix score.

## On Github Actions

- Exact reproducibility branch: `research/claude-handoff-global-angle-20261123`, PR #19.
- Executable GitHub Actions workflow: `.github/workflows/gvqcc-global-gauge-experiments.yml`.
- Public V8 compressed exact `angle_words` (1219 × 75) and `tree_edges` (75 × 2), with SHA256 integrity check: `fixtures/V8_C46_angles_edges_b85.json`.
- Original full V8 source NPZ SHA-256: `d4d39b2e2516ed7c51a936e863cf0567e558a0db8ded24e435f507d76bfb78d7`. Note the public fixture is **angle/tree only**, not full FeMoCo data.
- The workflow runs three global five-dimensional sign-gauge variants on public V8, and generates/locally verifies **real three-bank KMBs** for baseline, `all_flip`, and `address_bit6`. It also executes a separate global O(C)^R historical W/H2 study. Test artifacts include source and changed NPZ, KMB, SHA256, exact phase proof receipts and gate count.
- Historical W/H2 Actions job passed: https://github.com/corcondor/gvqcc/actions/runs/45057261569. R=8, B=143, C=44, lambda2 proxy unchanged 269.7683469146678, accepted orthogonal rotations 0, physical equalities 0 errors. **Not the C46 V8 parameter set**.
- For current actual V8 GitHub KMB execution, check workflow run status; no assertion of GH success until the logs confirm.

## Pattern K (exact physical sign freedom)

The 74 intermediate Givens sign bits have 70 independent stride-five signed6 constraints, yielding homogeneous dimension 4. For each address, a new binary variable `sigma` globally flips the sign of the complete 76-component vector; under pairwise contractions and projectors this is physically invariant. An affine GF(2) compensation equation gives a five-dimensional admissible family. All 1219 original V8 vectors were decoded and tested in independent local FeMoCo arithmetic.

| Sign policy | Different source angle words | Physical invariance |
|---|---:|---|
| all_one | 54287 | PASS |
| zero_first_msb | 26423 | PASS |
| select_addr_bit6 | 25910 | PASS |
| select_addr_bit10 | 8682 | PASS |
| gray_parity | 27105 | PASS |
| random | 27129 | PASS |

Maximum vector error 8.1e-16, FeMoCo relevant contraction differences ≤2.2e-12; the source lambda_eff is 46.918064099948054. **These changes are not themselves Toffoli improvements.**

## Real KMB measured comparison (local, all checked)

Using a common `signed6resid` 35-output synthesis backend, `J=5, lowbits=4`, compare real KMBs for **banks k=0..2 only**. All cases exhaust legal addresses, prove arbitrary initial target XOR behavior and exact symbolic HMR correction coefficients (not official native KickMix). Maximum quantum width for every case is 126.

| Variant | Three-bank Toffoli | Delta vs comparable baseline |
|---|---:|---:|
| original public V8 angle table | 840 | 0 |
| sign5 zero_first_msb | 871 | +31 |
| sign5 select_addr_bit10 | 841 | +1 |
| sign5 all_one | 859 | +19 |
| nonlocal B/R reindex-067 | 849 | +9 |
| same B/R reindex-067 AND sign5 addressbit10 | 851 | +11 |

The sign5+reindex comparison is **849 vs 851**, demonstrating no gain from the tested combination; it does NOT establish an impossibility bound on all co-optimized choices. Three-bank data cannot be extrapolated into a whole fifteen-bank score.

## Pattern O (FeMoCo full block orthogonal gauge)

For each block `r`, apply one and the same `O_r∈O(C)` to all of `W_r` and `H2_r`, maintaining `W_r W_r^T`, `W_r(H2_r−sum_b W_{r,b})`, and the relevant norms. Scanned 9 full V8 blocks × choose(46,2) = 9315 column pairs with 25-angle grid per pair. Accepted rotations 0; lambda2 proxy was 270.2168154149706 before and after. Exploratory whole-block SVD/QR/random orthogonal families worsened the proxy; no claimed global optimum.

## Archive (complete reproducible test material)

`GVQCC_GITHUB_CI_PATTERN_K_O_COMBINED_REAL_KMB_RESEARCH_20261123.zip` — 82 entries, 81 SHA256 manifest lines, verified all 81 plus ZIP CRC; SHA256:

`3b4015b223d322f1dabdf82ce7efcd754156b4fd606b6139198d6ad1358a9ad5`

Contains all original V8 15 angle KMB source, FeMoCo reference data, physically equivalent 6 alternative NPZ tables, the orthogonal test output, nonlocal B/R reindex candidate, 18 changed/existing first3-bank KMBs, all validators and raw receipts. The ZIP is supplied separately in the user conversation; it is NOT committed as binary into GitHub.

## Next distinct directions (implementation targets, not validated results)

1. **Exact compiler-cost guided sign-field synthesis**: select a separate representative of each of the 2^5 affine gauge classes *per address* using actual shared-XAG cache and KMB cost feedback. Do not optimize ANF rank only.
2. **Joint B/R ordering + angle-gauge and tensor factorization**: row permutation followed by physical residual refit and identical compiler comparison, preserving the actual oracle contract.
3. **Joint C45/R/B/C/J and W/H2**: evaluate physical error / lambda_eff plus actual 15-bank KMB and HMR structure; reject candidates failing 20mHa or FMOCO physical invariants.
4. **DQI + invsqrt nonlocal**: target peak-live restoration and reduced repeated arithmetic rather than isolated single CCX merges.
5. Independent official KickMix native value/phase/work-scratch check for all 18 final files before any score claims.
