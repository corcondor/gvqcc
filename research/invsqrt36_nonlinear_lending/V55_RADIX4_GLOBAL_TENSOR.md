# V55 — radix-4 global tensor architecture (NOT SUBMISSION)

Independent architecture, not a rewrite of the 37Q carry chain. Stacked on PR127. Donors PR123 (dyadic normalization), PR128/129 (sub37 dense-rotation diagnostics), PR126 (persistent nonlinear chart); no cross-parent arithmetic addition. User objective: competitive native circuit at any Q<37.

## Exact native results
All rows below are partial circuits / roundtrips with snapshots, not complete oracle implementations. Re-read serialized KMBs, test every legal x=1..3,133,452. Restore input and work wires. Where HMR is used, check each independent phase coefficient. No official verification or score.

| component | Q | paid CCX or expected paid | scope |
|---|---:|---:|---|
| radix2 cyclic / chain | 27 | 476 / 432 | normalize+inverse |
| radix4 cyclic / chain | 26 | 434 / 390 | normalize+inverse |
| measured radix4 | 26 | 238 expected (232 CCX +12 guarded CCZ at 1/2) | normalize+inverse |
| measured radix4 | 27..32 | 205,190,183,178,174,173 expected | normalize+inverse |
| original 125 coefficient bits, joint two-slice | 36 | 766 vs 830 independent | snapshots+restore, same coefficient function |
| measured + joint, 125 coefficient bits | 33,34,35,36 | 638,622,584,556 CCX | snapshots+restore |
| quantized coefficient grouping | 33,34,35,36 | 484,444,430,426 CCX | 109 nonconstant outputs, 16 constants; different model |
| low-width original coefficient stream | 27..31 | 5240,3217,2310,1481,652 CCX | 125 coefficient bits |
| first truncated product digit snapshots | 35 /36 | 7000 /6998 CCX | weighted sum, not canonical word, rejected |

Q26 normalizer SHA 7c92b2b5ed0d7fede60c2f8f6b8d22518310a44d971bcbfbf719a5690d528835. Q33 quantized loader SHA f22210c453fa6819e41d56e671c6d7687cd3ae3302cc9007659311ae783bd5dc (5170 ops,168 HMR). Q34 SHA 0089356f3045c5c64697cbbd187dacd45a7135162323d32f59dd48ba208db370. Q36 first product SHA d10e1f74485045d23b6efc24511e4e99bf67e9b5097356bab02e29077b7e1077 (19268 ops,332 HMR). Actual source template SHA cf1ba95ab89d6c745f13a0629f8638afd0e3e62b8c8168b6bd9362d8dd130d2b; header/parser reuse only, not arithmetic. All partial KMBs, exact snapshot ABIs, generators, logs and receipts in companion ZIP.

## New global algebra
x=4^e y, 1<=y<4, so invsqrt(x)=2^-e invsqrt(y). Shift by 16,8,4,2, record four Boolean decisions. On the normalized care set high pair a,b not 00, ab=1 XOR a XOR b. Thus three selectors are affine. Cache four nonlinear monomials of the low three address bits across all output groups; express output masks as affine high selectors times low ANF basis. For GF2 matrices A,B and common rank-one X, rewrite (A,B) into (A+X,B+X) with a shared X under XOR of selectors. When both ranks drop by one, product count falls by one. Exact rank reduction and emitted native replay, not a finite optimal tensor-rank theorem. Additional persistent mixed atoms k=1..4 were tested but none beat k=0 in the tested capacity model. Global set partition MILP on 109 nonconstant outputs, Q33..36 candidate counts 1907,2831,3188,3423, objectives 151,132,126,125; all solver status0 and lower bounds equal recorded objective. Optimum only within generated candidate family. Batches have snapshot ABI; consuming them is not solved.

## Exact integer approximation
104 configurations, 69 pass full-domain integer tolerance. 24 segments, degree4, F32, output B34: 31 generic rotation specification, ratio .8694607792; B35:32 generic, ratio .4454598039. Quantize coefficient columns by 1,2,3,4,5 bits and omit all low partial product columns below 17 at each of 4 multiplies. 1581 -> 969 candidate products (not CCX counts). Reference r=isqrt(2^130//x), target=(r+1)//2 mod2^64, tol=r>>25. Independent retained-term sum matches model on all 3,133,452 inputs. Worst ratio .9137239685366245, min slack 54096592, phase code SHA 51e4370ddd9b1029b69163aca604697c2b0130da63e9c49b774c6a61d47d9477. 31 generic rotations remain a mathematical spec only. Omitted product magnitude bounded by sum_{c=0}^{16}(c+1)2^c=2097153. No claim exact equality with original circuit. First product native arithmetic emits separate weighted digit sums, verifies all values but 6998 CCX at Q36 already exceeds entire proxy budget (~1470 paid at 31 rotations and selected margin). No score gain. Need carry-save/redundant digits with shared carry network and non-recomputing consumer ABI, not independently compute/uncompute each output column.

## Literature and scope
- OpenAI finite Fourier, Nov24 2026: https://github.com/openai/math/tree/main/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026 — predictor/repair and shared finite transforms motivate model and coefficients; no claimed asymptotic algorithm port or CCX bound.
- OpenAI matrix exponent nine fourths, Nov24 2026: https://github.com/openai/math/tree/main/preprints/The-matrix-multiplication-exponent-is-nine-fourths-November-24-2026 — finite common rank-one tensor factors used; no claim exponent 9/4 implies the observed finite GF2 synthesis or reversible cost.
- Khattar/Gidney conditional clean ancillae (arXiv:2407.17966); Gidney halving cost of quantum addition (arXiv:1709.06648): conditional input borrowing and measurement-assisted AND erasure used in native normalization. Quadratic relation transport and discrete Abel identities recorded; not full paper replication.
- New readings: Gidney windowed quantum arithmetic (arXiv:1905.07682), grouping lookup and arithmetic is a design motivation. In-place odd modular multiplication/inversion and hierarchical leading-zero counters were inspected at abstract level, not ported; odd modular operations do not directly implement high-bit truncated fixed-point products.

## Reproducibility and status
Companion GVQCC_V55_Radix4GlobalTensor_NOT_SUBMISSION.zip (328143 bytes before any archive revision), includes actual generators, KMBs, coefficients and receipts; local Lean identities and portable finite coefficient verification core in this branch. No full Lean proof, no official verifier/score. All ten #118 acceptance conditions remain open. Main/Kaggle untouched.