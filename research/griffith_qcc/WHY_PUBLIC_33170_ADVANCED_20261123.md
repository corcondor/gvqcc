# GVQCC 33.135 → Public 33.170: documented architecture change (2026-11-23)

**Baseline:** Goodpjw V8 public 33.13521306472748, hashes verified from source receipt. **Our own official-new score:** none; unchanged.

## Source read end-to-end

Read the **entire Markdown + executable cell source** of the Apache-2.0 public notebook by Mizero Lucky Gall: https://www.kaggle.com/code/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders . It explicitly credits **maoxin123** for the chemistry improvements and calls itself a *guided reproduction*, not a newly developed 33.170 algorithm.

Notebook Step 4 embeds compressed 15 KMBs and XOR-refitted W/H2; it does **not** contain the full matroid-parity generator. The following architecture details are grounded in the author's Markdown explanation, not a claim that every line of that generator was inspected.

## Exact cost and mechanism

* Chemistry: all 15 ANGLE banks **3,375 → 3,357 CCX per pass**, hence full T=13,250→13,214 and same 405Q. Public notebook's reweighted physics gives lambda_eff=46.91821075 and chemistry cost 251,090,780.94. Our Goodpjw baseline cost 251,774,061.476.
* **Unwired** batches: exact 96-product decomposition and delayed lower AND schedule.
* **Wired** batches: searched high cache, linear matroid parity (Lovász) over GF(2^16), FWHT, and GF(2) tail, with different output fanout/wiring geometry.
* Coefficients: active-set fixed-words Newton projection to saturate three physical accuracy gates; this is different from the 1e-10-sized local W/H2 changes we repeatedly tested.
* invsqrt: varianceofx's 3-T phase substitution on Rithvik Redrouthu 37Q parent. Algebraic phase identity -a+b-(a xor b)=-2a(1-b), using available nonlocal wire predicates and two Clifford S phases. Parent d2148a7c, replacement bb676b95. Cost about 60,955.3267→60,927.5767.
* DQI Tony Li 900Q 4b572141 unchanged. Public test zero errors is sampled, not a proof of all salts. Original lineage: Syed Asad Ali; preserve NOTICE.

Using full cost formula geometric mean and the published 33.170 component numbers gives approx **33.170277** versus 33.135213; this decomposes into the -36 chemistry T and -3 invsqrt T (plus very small lambda changes). **The public notebook** reports 33.17023 leaderboard; we did not reproduce its entire portfolio locally.

## Executed independent reproduction

We actually binary-patched the original d2148a7c KMB (SHA previously authenticated). Our custom v2 KMB writer first roundtripped the original **byte-identically**. Removing precisely the three Z_POW KMX lines 246, 255, 257 (KMB op offsets -23) and adding two S phases after KMX lines 10086 and 21025 produced the **exact published target SHA256**:
`bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`.

A full 18-file ZIP combined that exact invsqrt and 17 unchanged V8 files; checked every SHA, zip CRC and file count. With *previously reported costs for the unchanged files*, predicted GM **33.14024287579768**, delta +0.005029811; **no local native verifier or hosted Kaggle run**. Salt-dependent DQI score remains a risk. This is a **public-method reproduction**, not an original scoring record.

Research artifact in user conversation: `GVQCC_20261123_Public_33170_Source_Reading_and_Phase_Reproduction.zip` and `analysis_20261123/submission_public_phase_reproduction_18files_UNVERIFIED.zip`.

## Diagnosis of our failed research

1. Optimizing a simplified 5,050→4,866T XAG teacher is *not* progress against the actual 3,375T V8 KMB. Only costs from an emitter with competitive global caches and reversible schedule matter.
2. A giant equivalent Givens sign-gauge change is not cheaper unless the *new* words are recompiled cheaper.
3. A large fraction of chemistry T is not, by itself, evidence for choosing one track: optimize actual cost products and risk R(epsilon+) across all three tasks.
4. The public gain came from selecting *different algebraic models for wired vs unwired bank*, plus lifetime-aware scheduling, and exact provenance+verification, not from local peephole CCX removal.
5. A source-level gap remains: obtain or re-implement the exact Lovász GF(2^16) matroid-parity compiler, not merely its 15 output blobs. Only an exact new 15-KMB emission and native verified scoring can constitute independent progress beyond 33.170.
