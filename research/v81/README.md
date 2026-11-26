# V81 finite-field classification and reversible additive scan (research only)

Refs #163, #169, #170 and V80. No official score or whole-DQI improvement claimed. No new 900Q candidate.

## Actual native result

This component's ABI is 35 non-leading coefficients of a monic locator P, 35 coefficients of a magnitude interpolant V, each in GF(2^12) with modulus 0x1053, and 4095 classical 12-bit masks. Its exact phase is the XOR of mask dot V(x) for every nonzero x with P(x)=0. For weight w<35 pad the locator with X^(35-w); the extra root 0 is excluded. The input is NOT the competition syndrome ABI. The forward syndrome-to-(P,V) and its inverse remain unimplemented.

| Native stage | Q | CCX | HMR | Instructions |
|---|---:|---:|---:|---:|
| rolling evaluation (new matched control) | 851 | 45045 | 45045 | 23085359 |
| additive FFT, direct field matrices | 851 | 45045 | 45045 | 3515411 |
| additive FFT, shared parity synthesis | 851 | 45045 | 45045 | 3026775 |

Final CX=2775524, SWAP=298, X=1158. SHA256 ec3f2adcae920dcafcba0810d12e0a9b09b56df7a0feb4678159108067a3f252. All three serialized KMBs independently checked at all 4095 nonzero points: exact 841-bit affine rows (840 input bits plus constant), restored input, clean scratch, structural HMR correction for every outcome. Independent 64 packed sparse-error cases include weights 0..35 and zero/one-hot masks; zero value/phase mismatches. Both methods execute mean CCX 44331 on these fixtures. This is not the official DQI distribution or verifier. The 86.89% instruction improvement is relative to the newly generated rolling control, not the existing 68M-instruction full decoder. Native KMBs and full comparison logs are in the companion archive.

## Classification and transport

Mathlib v4.35.0: GaloisField, Extension, Trace. The subfield degrees are exactly divisors of 12, fixed by the corresponding Frobenius. Enumerated all eight subfield chains, plus polynomial and normal bases, 100 tree/physical-basis pairs under a linear-gate estimate. Best: tree 1->2->4->12, physical polynomial basis. Tree beta = [1,70,1971,2939,2,140,3942,1701,4,280,3743,3402]. The concrete modulus is separately checked by generating all 4095 nonzero elements; 4096 trace-dual masks are bijective. The winning emitter uses polynomial coordinates directly. Other physical bases were screened, not all emitted; the estimate is not an optimality certificate.

For H_i=span(beta_0,...,beta_{i-1}), use T_i(X)=product_{h in H_i}(X-h), normalized S_i=T_i/T_i(beta_i). In characteristic two T_{i+1}=T_i^2+T_i(beta_i)T_i. The branch update a -> a+c*p -> a+(c+1)*p -> a restores all coefficients, permitting both polynomial evaluations in the original input space. Each field scalar multiplication is a binary linear map; reversible shared parities reduce actual CX. Leaf: 11 clean conjunction products, classical-mask-controlled CZ phase, HMR with exact conditional CZ cancellation. FieldTransport.lean uses actual mathlib finite-field embedding/cardinality/trace theorems and proves the abstract recurrence, discrete restoration, and half-Bezout identity. No full circuit Lean proof claimed.

References: [Mathlib GaloisField](https://github.com/leanprover-community/mathlib4/blob/v4.35.0/Mathlib/FieldTheory/Finite/GaloisField.lean), [Extension](https://github.com/leanprover-community/mathlib4/blob/v4.35.0/Mathlib/FieldTheory/Finite/Extension.lean), [Trace](https://github.com/leanprover-community/mathlib4/blob/v4.35.0/Mathlib/FieldTheory/Finite/Trace.lean); Gao–Mateer (2010), https://www.math.clemson.edu/~sgao/papers/GM10.pdf ; Lin–Chung–Han (2014), https://arxiv.org/abs/1404.3458 ; Coxon (2021), DOI 10.1016/j.jsc.2020.10.002 ; Samanta–Badakhshan–Gong (2026), https://arxiv.org/abs/2608.20855 . The implementation is a reversible depth-first normalized subspace butterfly with physical parity synthesis, not a reproduction of every algorithm in these papers.

## Actual whole-parent analysis (negative)

Read the complete V78 dqi_shear.kmb: 900Q, 68790003 instructions, 312234 CCX including guarded, 318950 static three-qubit paid operations, SHA256 ef2a1258783ce61ebca645c162d8c54e54ddd3f7ff96faa25b13e9dcb633364e. Full scan of 311838 unconditional CCX with bounded differential debt transport: zero accepted deletions. Full quadratic block scan: 6501 runs, 1412 qualified (56590 CCX), zero dependencies or savings. These are restricted experiments, not lower bounds. No rewritten full 900Q circuit was emitted. Review dqi_algebra_report.md and symmetry_dqi_mixed42_20261115_report.md for prior negative 99/42 product decompositions.

## Reproduce (Linux, GCC)
```sh
cd research/v81
python3 field_scan.py
g++ -O3 -std=c++17 emit_opt.cpp -o emit_opt
g++ -O3 -std=c++17 check_scan.cpp -o check_scan
python3 fixture.py
./emit_opt additive additive851_opt.kmb
./check_scan additive851_opt.kmb fixture.bin
./emit_opt rolling rolling851.kmb
./check_scan rolling851.kmb fixture.bin
cd lean
lake update
lake exe cache get
lake build
```

No official score, no official verifier, no whole DQI <900Q candidate; no main/Kaggle mutation.