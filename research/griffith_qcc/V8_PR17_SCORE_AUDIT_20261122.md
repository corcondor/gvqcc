# V8 / Griffith joint-XAG score audit (2026-11-22)

**Status: NO NEW OFFICIAL SCORE. Do not merge as a scoring improvement.**

## Scorable baseline versus numerically passing H2-only candidate

The previously recovered Goodpjw V8 has published local score `33.13521306472748`, chemistry `lambda_eff=46.918064099948054`, 15 ANGLE KMBs totalling **3,375 CCX per pass**, chemistry 405 qubits, and reference checks in the public receipt.

An existing 18-file H2-only candidate was re-audited against that receipt:
- 17/17 KMB SHA-256 hashes match the verified public source **byte-for-byte**.
- The NPZ schema, `W`, `angle_words`, orbital tree and fixed shifts match; only `H2_I` differs.
- An independent FeMoCo numerical evaluator gives `lambda_eff=46.918063993054645`, `error_1=0.019999999975788885`, `error_2=0.019999999949929688`, `E_gap=3.9148980001154996`, `Lambda=283.10203166752785`: **physical PASS**.
- Assuming the identical KMBs imply unchanged T/Q and original score components, geometric-mean extrapolation gives **33.13521308989146**, delta **+2.5164e-8**. This is a **prediction**, not a newly native-verified result, and not competitively meaningful.
- The H2 candidate is a **pre-existing** Library bundle, not a novel score update in this experiment.

## New exact search work

- Swept **all 2,048 input addresses** for 15 V8 ANGLE loaders and 3,375 CCX gates. A conservative abstract-dependency pass tracks 35 arbitrary dirty output target inputs: **0 statically certifiable CCX always-zero actions**.
- On the same full-address bit-vector states, attempted to replace each CCX control product with the GF(2) linear span of presently available clean qubit values (excluding the target). **0 conservatively certifiable affine replacements.** This does not prove absence of non-affine, time-retimed or dirty-dependent resynthesis opportunities.
- Tried analytic-gradient H2 optimization and orthogonal `W,H2_I` gauges: no meaningful feasible cost reduction. H2-only 18-point line scan accepted only the baseline and the pre-existing endpoint; interpolation lost the strict `E_gap` margin, extrapolation violated `error_1`.
- Separately evaluated a recovered C45 proposal: `error_1=0.0226066464`, `error_2=0.0291273230`, `E_gap=2.69417914`: **physical FAIL**; not for submission.
- Attempted to project the stronger `lambda_eff=46.9137590418` physical candidate onto the unchanged public-loader table; `error_1=0.0222785 > 0.020`, so the old 15 KMBs cannot be reused.

## Reproducible artifacts

The user has a research audit ZIP in the current conversation (`GVQCC_V8_PR17_Score_Audit_20261122.zip`) containing:
`verify_18file_h2_candidate.py`, `h2_line_search.py`,
`ccx_zero_exhaustive.py`, `affine_replace_ccx.py`,
`physics.py`, source receipts and SHA-256 verification manifest.

It requires the original published V8 reference, existing H2-only 18-file ZIP and an authorized FeMoCo reference NPZ. No external reference matrices or giant third-party circuits are committed.

## Next scoring gate

An actual competitive improvement requires **fewer real KMB CCX / lower peak Q**, a proven full 15-bank reversible phase/workspace schedule, and native KickMix 78,016-shot chemistry plus DQI/invsqrt verification. The local Griffith four-bit one-AND witness is a useful algebraic result but cannot be counted as a 15-bank Toffoli saving.

**No Kaggle submission or native KickMix score was performed in this session.**

## Quantified target (other components and chemistry Q / lambda fixed)

Using the published baseline chemistry T=13,250 and 3,375 ANGLE Toffolis per pass (called twice), the aggregate-score geometric mean requires:
- **33.5:** total chemistry T <= 12,821.85; thus ANGLE < **3,161 T/pass** (at least 215 T/pass saving).
- **34.0:** total chemistry T <= 12,264.46; thus ANGLE < **2,883 T/pass** (at least 493 T/pass saving).
- Merely finding a 1-AND local cut is not enough. Cross-bank persistent state and exact phase/workspace schedule determine whether real cost decreases.
