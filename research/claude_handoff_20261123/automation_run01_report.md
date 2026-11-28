# GVQCC: 2026-11-23 03:40 JST, independent structural audit run 01

**Verdict: NO new officially verified score and 0/3 verified independent gains.**
Benchmarks preserved: last user-reported officially verified score **33.13521306472748**, public target **33.17023**. Do not count a local invariant or a reconstructed KMB as a score.

## Three distinct experiments with real original KMB/NPZ

1. **ANGLE / nonlinear CCX guards:** exact 1219-valid-address, 15-bank sequential bitset simulation on **real C46 V8 15 KMB (3357 CCX, 128Q)**, with each bank's 35-angle-bit output, scratch, and HMR phase coefficient locally matching. All 3357 CCX guards are active for at least one valid address; **0 dead gates, 0 gates trivially reducible to CNOT, 0 always-on gates**, also 2048 full address-encoding guards active. This eliminates naive *constant-gate* deletion, not multioutput resynthesis / sharing. Each bank SHA256 saved in the local scorecard.

2. **Chemistry / full W-H2 O(46) gauge:** implemented 9-block Jacobi plane-rotation coordinate descent with 12 angles and up to 16 greedy sweeps each, minimizing actual L1-based lambda2, checking FeMoCo two-/one-body physical reference (no proxy ANF rank). **0 rotations accepted**; lambda2 **270.2168154149706** and lambda_eff **46.918064099948054** unchanged; e1/e2 ≈ 20 mHa, old C46 15 KMB **3357T/128Q** unchanged. Non-winning output NPZ reserialized with SHA; a different byte checksum does *not* indicate changed numerical factorization.

3. **invsqrt / conservative HMR-aware workspace live intervals and conditional phase:** original **37Q (22 input +15 scratch)**; scratch lifetimes overlap pairwise, all 15 simultaneously potentially live across **24,101 KMB op positions**. Trivial interval coloring alone does not reduce to 36Q; does not prohibit new schedules, recomputation or phase correction. Conditioned 3T->S search: no suitable single-wire on-time representation in 30-op local window for group0 on fixed HMR=1 branch; group1 scope=0, so any candidate from this branch would be a vacuous false positive.

## CRITICAL safety retraction: invalid 9T invsqrt change
The older '9T->4S' rewrite did **not** preserve all HMR branches. Removed T gates are guarded by classical b743 while inserted S gates are unconditional. Reproduced **383 phase mismatches among 1024 inputs** on all-HMR-zero, including x=0. Older whole-domain results showed **1,300,770** branch0 and **749,964** branch1 mismatches across 3,133,453 inputs. **This KMB is UNSAFE: never submit or call verified.** Updated parent README with this retraction (commit `3aec243e7b5888f2e94e22aa44c91ef1eecacafe`).

## Deliverables
- Reproducible zipped bundle: `GVQCC_20261123_run01_structural_negative_audits.zip` (available as a verified ChatGPT conversation artifact, not yet hosted on GitHub).
- Exact ZIP SHA256: `d049b3c8cd99edf4a006584399dd878fb5474e5f2e6ecea9a322362288f1f7d1`.
- 44 included inputs, outputs and scripts, all file hashes in internal `bundle/SHA256_MANIFEST.json`.
- Contents: original 15 KMB, original C46 NPZ, physical reference data, original 37Q invsqrt KMB, 4 original audit programs and regression checker, result JSON, logs, and reproduction commands.
- **Clean extraction/clean run passed**: `cd bundle/run01 && bash REPRODUCE.sh`. Tests assert unsafety of old candidate, 15-bank local invariants, absence of guard-zero, unchanged physical reference, conservative workspace overlap, and vacuous branch screening.

No actual new lower-cost KMB was found. This run produced audits and a reserialized no-change NPZ, not a winning changed circuit. **Official KickMix not available/executed.** Remain in research status and keep scanning for genuinely different cost-driven nonlinear ANGLE, DQI nonlocal, invsqrt rematerialization candidates. Do not confuse this negative work with a score improvement.