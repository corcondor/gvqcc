# Compiler-in-loop exact-gauge experiment — 2026-11-22

Status: **no new native KickMix score**. Public Goodpjw V8 remains 33.13521306472748. All figures below are real executed model synthesis checks, **not** native V8 replacement KMBs.

The 15-bank public V8 KMBs were parsed independently; each SHA-256 matches the public receipt, summed ANGLE 3,375 CCX/pass, including bank 0 = 246, bank 1 = 241. W/H2 and gate counts are separate objectives and must never be conflated.

### Actual source-code experiment and exact certificates

- Replayed Griffith temporal helper LUT GF(2) sign-gauge projection with every row of public 1219x75 seven-bit angle table, 9 exact helper mutations. All recomputed 76-dimensional orbital vectors agree up to a global sign (maximum normality error 6.67e-16).
- A bit-4 helper mutation changes 2,414 angle table cells while preserving the independent FeMoCo metrics:
  - e1 0.019999999949999993 -> 0.019999999950000135 Ha
  - e2 0.019999999949929688 -> 0.019999999949929688 Ha
  - lambda_eff remains 46.918064099948054
  - both numerical physical gates PASS.
- Fed the real V8 delta tables into an exact 4-low/7-high GF(2) multioutput XOR-AND compiler (same teacher, same seed 0, one trial, all care-address bits exact). Cost **includes 80 cached monomial CCX**:
  - bank 0 word order 310 CCX; plane 328; 1-bit gauge mutation word order 310.
  - bank 1 word order 314; joint reordered bit1-first 297; plane-reversed 329; 1-bit gauge mutation word order 327.
  - **17 fewer model CCX** in bank 1 after output regrouping; all mixed ANF tensors exactly reproduced.
- Caveat: new model's 297 CCX is **still 56 worse** than the actual public KMB's 241 CCX for bank 1. The research changes do not beat the public circuits; changed angle words invalidate all original ANGLE KMBs.

Repro package retained as conversation file `GVQCC_20261122_ActualCompilerFeedback_Experiment.zip`, ZIP SHA256 `bd0e725d0aae4a4482f6a93bda31ec874829681e25673d175bf4011c1fd979bd`, 21 files. Includes runnable `compiler_feedback.py`, `explore_layout.py`, `gauge_physics_verify.py`, inputs, compiled-tensor verification, receipts, and full SHA256 manifest. Neither submission nor native verifier has run.

### Implication

The desired joint learner **must** optimize directly against *real emitted V8-competitive reversible KMB* cost, including 128Q sharing/pebbling/HMR and the 15-bank temporal state. The present product-cache compiler is a losing teacher; reducing its model CCX alone is not score improvement. Continuous W/H2 optimization was not part of this new experiment and is not claimed.

Main untouched; no official score update.
