# GVQCC V8 multi-variable ANGLE/W exploration — 2026-11-23

**Result: no new native KickMix score.** Do not count any XAG proxy optimization as scoring improvement; public Goodpjw V8 remains the reference 33.13521306472748.

## Executed, independently verified measurements

Baseline public chemistry ANGLE 15 KMBs: **3,375 native CCX per pass** (source KMBs unchanged). Baseline FeMoCo independently checked `e1≈0.01999999995, e2≈0.01999999995, λeff=46.918064099948054`.

- **30,000** randomized C46 orthogonal multi-axis W/H2 gauge moves: **0 improvements accepted**; this does *not* constitute meaningful motion in W or new physical wavefunction training.
- **1,000** 80-bit helper-code randomized proposals, 990 evaluated, GF2 rank proxy flat 7,175. Metric rejected as training guidance.
- **4,000** helper-sign-gauge multi-output ANF-weight trials, 3,968 evaluated: 270,966 → 269,170 ANF nonzeros, angle table 38,070 cells changed. Physics unchanged up to global signs, not a score.
- Discovered **32 independent pure-π Givens sign degrees** from the 76-component carrier tree. Pure bit6 (XOR64) gauge search of **900** exact projections changed 37,944 / (1219×75) angle words; all low six bits identical, max orbital error up to global sign `6.106226635438361e-16`.
- Full 15-bank **symbolic** GF2 rank-factorized XAG count: **5,050 → 4,866 CCX/pass** (all mixed tensors exact). This is still **1,491 CCX/pass worse than native V8 3,375**, and no new phase-valid KMB has been built. Do not equate proxy CCX with actual hardware score.
- **9,315** exact-piecewise two-column orthogonal W/H2 gauge rotations scanned all breakpoints and interval minimizers. Best improvements were only ≤1.14×10^-10 per block (numerical-noise scale). No meaningfully better W.
- C46→C45 whole-block SVD smallest singular direction drop numerically failed: e1=20.4214839mHa and e2=24.0001059mHa. Dropping the smallest-norm existing column also failed (e1=1344mHa, e2=386mHa).
- Combining new pure-π angle table with a **previously available** physical-pass W/H2 update gave `λeff=46.918063968226534`, independently verified FeMoCo PASS. W magnitude change is tiny (L2 4.88e-7) and no new joint W training converged. The 15 original native KMBs do **not** encode this changed angle table, so this is **not submit-ready and is not a new score**.
- A conservative single-CCX deletion scan on native ANGLE bank KMBs found zero phase-safe physical-deletion savings in the screened subset, not a global impossibility proof.

## Reproducibility / adoption rule

Current conversation contains `GVQCC_V8_ANGLE_37944_W_Joint_Experiment_20261123_NO_SCORE_GAIN.zip` (82 files, 28.18 MB, SHA256 `ff81a93d3a5058ad16a68de5cf805bad403fd332fd9c78f852a71106d8ce17fb`), with 15 public native ANGLE KMBs, baseline submission.npz, FeMoCo reference tensors, changed data, source, result traces, and a portable `REPRODUCE.py`.

The portable script was run; confirmed exact GF2 15-bank symbolic CCX 5050/4866, public KMB CCX 3375, all 1219×75 gauge equivalence and independent FeMoCo physics. Official KickMix score and phase verification **not performed**. Main branch untouched.

The next measurable advancement must (i) create materially different discrete angle words and retrain physical W/H2 to strictly satisfy error/gap constraints, or (ii) emit an actual V8-better reversible full 15-bank KMB. Merely increasing trials in a flat proxy or applying physics-preserving gauge does not count.
