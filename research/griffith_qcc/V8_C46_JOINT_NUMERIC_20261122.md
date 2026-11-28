# 2026-11-22 V8 score sprint: actual full-chemistry C46 joint coefficient update

**Status: new numeric candidate, NOT a native KickMix score improvement.** Do not merge or submit without native verification.

## Source / baseline
- Existing Goodpjw V8 public receipt: 33.13521306472748 reported; chemistry 13,250T / 405Q; 15 ANGLE loaders total 3,375 CCX per pass.
- V8 18-file source is unchanged: all 17 KMB SHA-256 hashes match its receipt byte-for-byte.
- Prior H2-only candidate `lambda_eff=46.918063993054645`, independent physics PASS, predicted score `33.13521308989146`.

## Newly executed full C46 optimizer
- Added a new local source artifact `optimize_v8_w_feasible.py`: optimizes all nonzero `W` jointly with `H2_I`, holding `d=H2_I-sum_b W` and `sum_c d_rc Delta W_rbc=0` to preserve one-electron terms and energy gap. The C46 and 7-bit words remain unchanged.
- Exact reference residual `R0=X0.T X0 - T` and incremental quadratic / quartic e2 algebra avoid catastrophic cancellation of large tensor norms. The derivative of e2 squared was checked against finite differences.
- Pin nearzero W and H2 values at absolute-value kinks to avoid false smooth `L1` gradients. Feasible normal corrections keep absolute FeMoCo two-body error below 20mHa.
- Numerical outcome from the existing H2 candidate: `lambda_eff 46.918063993054645 -> 46.918063968226534`, `error_1=0.01999999997578904`, `error_2=0.019999999975004474`, `E_gap=3.9148980001154996`: independent physical PASS.
- New 18-member research ZIP SHA-256 `30161b355af06fb8a4f770e0e87f86f51466f1b40bab04d24964cc5c881282a3`; 17 KMBs unchanged.
- Score **predicted only** `33.13521309573629`, just `+5.844832e-9` over preceding unverified candidate. Competitively negligible; not an observed new KickMix score.

## Other new actual circuit audits
- All fifteen verified V8 loaders, 3,375 CCX in total: commuting same-product fanout reductions **0**; dirty-aware bit-slice search for replacing individual CCX with available affine wire sums **0**; consecutive 2 and 3 CCX quadratic reductions across CX-only stretches **0**.
- An additional independent scan of all 75 angle columns found minimum `||T2(new)-T2(old)||=0.048642746` Ha for a global one-column bit0 flip with W fixed. This exceeds 0.040, the necessary triangle-inequality bound for *both* tensor approximations to be within 20mHa. It says nothing about a joint W retrain.
- The negative scans are bounded to their specific algebraic models and do not prove global optimality.

## Reproducibility
Local conversation artifacts:
1. `GVQCC_V8_Score_Sprint_20261122_SOURCE_AND_NUMERIC_CANDIDATE.zip` (the new optimizer source, independent physics code, search scripts, JSON trace, NPZ);
2. `GVQCC_V8_C46_W_H2_NEW_NUMERICAL_PASS_NATIVE_PENDING_20261122.zip` (full 18 files with the modified chemistry NPZ).
No KMB count, qubit count, phase schedule or official score is claimed improved. Kaggle not submitted, main branch untouched.
