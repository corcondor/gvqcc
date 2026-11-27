# 316k HMR phase-only witness repair (REJECTED — NOT SUBMISSION)

This experiment is on the exact 900Q, 62,086,097-instruction donor SHA256 `2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60`, NOT the different 69,782,188-instruction 316k donor.

## Exact structural finding
The first failing phase coefficient (measurement ordinal 70, instruction 19581639, q7, bit 49140) measures a wire whose formal Boolean expression is identically zero with all 840 original S input bits independent. XOR and repeated product expressions are tracked; rebasing and conditional updates conservatively forget nonlinear relations, never infer an equality from sampled input. The HMR phase is m*x, and x=0 implies it is zero. For an outcome SSA lifetime used exclusively by directly conditioned phase gates, any remaining dependence on that outcome is spurious. A nonconstant overwrite, classical control-stack use, conditional overwrite or value-gate use disqualifies the candidate. All 49,140 external mask bits excluded.

Full-tape scan: 687 provably-zero unconditional HMRs, 372 eligible phase-only lifetimes, 56,942 conditional phase instructions removed (one static paid); no original HMR, computational value instruction, or external mask changed. Complete emitted candidate SHA256 `e45e3a8dacff49063c1cfc9d1a65cd4d4d6c939fd6429b164e228a3ea5bcf615`, 900Q, 62,029,155 ops, 318,583 static paid.

## Rejection
Exact single-event-flip history audit: w0 phase mismatches 308 -> 203, w1 695 -> 639, w17 112 -> 111, w18 and w35 both 0 -> 0. Restoration bit mismatches remain 0,395,430,0,0. This is not all-history verification. Independent actual KickMix paired replay of the same 72 legal inputs (weights 0..35 twice): BOTH parent and candidate 34 value errors, 19 phase errors, including two phase errors on restored inputs, zero dirty errors. Diagnostic average paid 316065.02777777775 -> 316064.5416666667. No new score or accepted candidate. An additional exact affine/product witness search at 1045 known problematic measurement ordinals found no eligible nonzero witness in this abstraction. It is not a general lower bound. The zero-mask five-input/four-seed panel also still fails.

The mathematical requirement for the remaining HMR is to preserve the actual pre-measurement function x and cancel m*x, rather than an inverse-chart prediction xhat: remaining debt m*(x XOR xhat). If x is not recoverable in the live state, changing only the phase polynomial cannot in general repair the oracle. The forward arithmetic and reverse map must preserve sufficient information; no sign-error-free 316k submission is claimed.

See separately supplied research ZIP for exact scanner/splice source, input map, selected SSA epochs, raw logs and native receipts. No submission or main merge.
