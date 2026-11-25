# Persistent tensor transport under strict width bound (NOT SUBMISSION)

Parent #128. Full independently re-read 32Q and 34Q native diagnostic circuits, not competitive replacements.

| Q | CCX before → after | Operations before → after | HMR before → after | Arbitrary rotations before → after |
|---:|---|---|---|---|
| 34 | 21820 → 20564 | 258639 → 164907 | 5340 → 1040 | 5399 → 5390 |
| 32 | 21591 → 20526 | 254083 → 152705 | 5514 → 928 | 5573 → 5568 |

The output SHA-256 digests:
- 34Q: 79f8421736901ac15c5499b51f5299cd6a7235455cdf0becad1c7473df2a3930
- 32Q: a3e72541b103f427aae0e88ad5052192c66aefb58b28a25feb17a27b481b4726

All 2^22 input controls, all independent HMR branches, input/scratch restoration and exact rounded spectral phase on the full cube PASS. Squared relative tolerance on all 3,133,452 legal inputs PASS; worst ratio 0.8125815968960524. No 37Q emitted. No official verifier/score claim.

For one-hot prefix flags f and input x, the carrier is f^T A x XOR c^T f. A rank-r factorization of A XOR A' realizes transport to the next carrier using r CCX, parity basis conjugation, and free affine updates. HMR resets with the exact conditional quadratic phase correction are alternative edges. A greedy rank-aware route and duplicate-control merge were tested. Not globally optimal.

The full executable bundle GVQCC_Sub36_TensorTransport_NOT_SUBMISSION.zip supplied in the research conversation includes tested compiler, dependencies, parent KMBs, emitted KMBs, tags, logs, manifests, and receipts. This PR contains the algebraic certificate and reproducibility record, not the binary archive. Lean checks are elementary Boolean identities, not formalization of native simulation; CI status must be checked separately.

References consulted (not direct implementations of the asymptotic algorithms):
- OpenAI, The logarithmic exponent of finite Fourier transforms, 2026-11-24, repair and kernel sections: https://github.com/openai/math/tree/main/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026
- OpenAI, The matrix multiplication exponent is nine fourths, 2026-11-24, local concentration and shaving sections: https://github.com/openai/math/tree/main/preprints/The-matrix-multiplication-exponent-is-nine-fourths-November-24-2026

The finite GF(2) factorization is not an application of the claimed asymptotic exponent to reversible gate counts. Thousands of rotations and >20k CCX remain; the competitive sub-36Q solution is open. Main and Kaggle unchanged.
