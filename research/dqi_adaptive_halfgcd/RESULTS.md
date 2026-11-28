# PR303 research receipts (2026-11-28)

Strict Lean CI: https://github.com/corcondor/gvqcc/actions/runs/46141514596 — PASS on 2769c7ed3d58bccbf3888cabc352cc44fcf0b98e. 138 checked declarations, including 38 new AdaptiveHalfGCD declarations, 100 inherited declarations. This is component algebra, not an end-to-end KMB correctness proof.

## Native KickMix components

| Component | Q | Instructions | Static paid | CCX | CSWAP | Paired forward/inverse shots | Errors |
|---|---:|---:|---:|---:|---:|---:|---|
| Adaptive division (17,16) | 468 | 180876 | 8904 | 6280 | 2624 | 576 | all six zero |
| Adaptive division (35,33) | 899 | 614918 | 23828 | 17632 | 6196 | 1120 | all six zero |
| Adaptive division (35,22) | 765 | 537307 | 18842 | 15234 | 3608 | 768 | all six zero |
| Adaptive division (52,17) | 900 | 753017 | 31626 | 28950 | 2676 | 608 | all six zero |
| In-place reciprocal (70) | 889 | 1809412 | 55836 | 55836 | 0 | 384 | all six zero |
| Packed extraction first stage (70) | 900 | 3358582 | 102180 | 91548 | 10632 | 3472 | all six zero |

Division (35,33) baseline 37710 paid; reciprocal baseline 82908 CCX; first-stage baseline 105402 paid. Zero-divisor branch totalized as identity. Reciprocal on zero constant is a separate totalized map, not division by zero. First-stage cached valuation covers legal v<=34 and zero input. First stage tests 1440 saved inputs and 296 synthetic cases, both directions.

Forward KMB SHA256:
- division (35,33): ccdf45f5fff9b64c1bca818a0cb3ab1334bd4247e8997f5895a7711fa6215e8a
- reciprocal (70): 3fdaab78fa454f2a7b25103a811679f8de982968fc048370cf565d99454016b7
- packed extraction: a57cd0d225cc7f62f7315ba60c6dc3f85d2b09bb16a3abc378063bc9b29cf653

Native generators, KMBs, logs, detailed receipts and reproducibility instructions are provided in the separate research ZIP (GVQCC_PR303_AdaptiveHalfGCD_RESEARCH_ONLY.zip), not committed here.

## Classical balanced half-Pade reference

For a legal balanced moment series f=N/D of precision 2q, take v=ord(f), a=leading coefficient, U=f/(a X^v), and U^-1=H+X^(v+2) f_next, deg H <= v+1. Retire exactly 2(v+1) words, reduce q by v+1, and reconstruct f=a X^v/(H+X^(v+2) f_next). A naive single-constant continued-fraction step was rejected on high-valuation input.

Batched recursion using joint and transposed middle products plus Newton reciprocal: all 1440 saved inputs matched syndrome and reference phase. Mean field products 2822.0229167 -> 1987.7326389, excluding final reconstruction and phase scan; classical zero shortcuts are data dependent, so these counts are NOT physical CCX. Naive explicit matrix storage still peaks at 142 words (1704 data qubits). No complete coherent recursion.

If det M=lambda X^K and (a*s0+b)=X^K A, (c*s0+d)=X^K C, the next packed lift is (A+a*t)/(C+c*t), with a*C-c*A=lambda. This is a candidate for compressed first-row/Bezout transport, not yet lowered to a full DQI circuit.

## Score budget only

Holding other PR292 public-reference costs and DQI effective error factor fixed: estimated aggregate 33.33550888098839. At 900Q, target 33.36 requires DQI mean <=315432.935721981 vs reference 316128.67875 (saving ~695.743). At 899Q with identical mean and error factor, conditional estimate 33.360224736995164. No 899Q complete tape, official re-verification, or score improvement claimed.

**RESEARCH ONLY — DO NOT SUBMIT.** Whole-oracle integration, global width, phase and inverse cleanup, full 102400-shot verification remain outstanding.