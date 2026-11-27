# Half-degree Bezout magnitude coordinates (research only)

A new native stage replaces per-point field inversion by polynomial preprocessing and a 4095-point additive-FFT phase scan. It is **not a complete syndrome-input DQI circuit** and is not a submission.

- forward: 840Q, 24486 static paid, 313767 ops, 406/406 native PASS.
- forward/phase/inverse: 851Q, 94017 static paid, 3900081 ops, 406/406 native PASS, diagnostic mean paid 75816.71428571429.
- Inputs from 203 syndrome-only classical BM/half-coordinate constructions, weights 0 through 35, two seeds. Native input is (D,H), not the original syndrome. Native decoder and two degree-17 modular multiplications remain missing.
- Exact hashes and results: half_receipt.json.
- Reuse #171 additive FFT, #237 GF(4096) 42-CCX tensor, and #244 general rational framework. The new stage eliminates per-point inversion rather than appending special cases.

## Algebra

Pad locator D and numerator P by the same squarefree product of distinct root-free quadratics (and X for odd degree). The degree-35 locator remains squarefree. Write D=A²+XB², P=P0²+XP1². B is monic degree 17; gcd(A,B)=1. Solve U=A^-1 P0 mod B and T=A^-1 P1 mod B, Z=(P0+AU)/B, W=(P1+AT)/B. Then B²[(Z+XT)²+X(W+U)²]=P+D(U²+XT²). At each nonzero locator root the resulting polynomial V is x*e(x); absorb x^-1 in classical phase masks. The triangular frame H=(leading P0 coefficient,T,U) -> V is implemented reversibly. The upstream syndrome-to-H calculation is still classical in this experiment. The Lean file certifies algebraic lemmas, not full physical composition.

## Reproduction

From this directory (KickMix 1.0.0, NumPy, C++17 compiler):

```sh
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/d442f72507472f5d4e1bce77a07f08ab1da2b16f/research/v81/field_scan.py -o field_scan.py
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/d442f72507472f5d4e1bce77a07f08ab1da2b16f/research/v81/emit_opt.cpp -o emit_opt.cpp
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/a52fe81aa92f19b907e3c85813e49998523e1eae/research/dqi316k_joint_crt/crt882.py -o crt882.py
python field_scan.py
python build_half.py
g++ -O3 -std=c++17 half_magnitude.cpp -o half_magnitude
./half_magnitude forward forward.kmb
./half_magnitude half half.kmb
python finalize_kmb.py
python verify_half.py
```

Vercel test used zig C++17 compiler; the CI checks hash-identical reconstruction. No official score is claimed. Do not replace donor or submit until full legal syndrome-to-H-to-phase-to-syndrome path is native and independently verified.
