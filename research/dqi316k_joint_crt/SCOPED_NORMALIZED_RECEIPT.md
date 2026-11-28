# Vercel experiment receipt — 2026-11-28 JST

Research only. Do not submit or merge to main. Vercel sandbox sbx_ZbMGKVBmW9PhpUK44YkEo9ROoay5 (4 vCPUs, 8 GB). Upstream Tony Li Apache-2.0 dataset version 2, exact donor rebuild with KickMix 1.0.0 pip wheel on Python 3.14 (competition 3.13 .so not loadable in this environment). All candidate metrics below are native KMB replays or explicitly labeled algebra tests, not Kaggle leaderboard submissions.

## Whole-tape candidates

- Donor: 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52; 900 Q; 69,782,188 instructions; 318,972 static paid.
- Scoped constant propagation with reset/HMR retained: 9d3c30a10b409458a749a78c8f434508568dafcaf369f43d3ba4d3afef1eb3dd; 900 Q; 69,709,262 instructions; 318,333 static paid.
- #239 direct commuting + scoped propagation: 1b738200420995367bed19bf6b8a2bba198a9f17f92ce2fae1d3edaaf561258f; 900 Q; 66,708,642 instructions; 318,333 static paid.
- Reset-removing candidate 4dc6e0eae719d6d350ba599331d6db93f39469a779d438d44908dd109a1be5a3 rejected: 248/1024 raw phase outputs differ with paired seed on forced panel.
- Paired seed 202611280745, independent native evaluator score_pair.py, same inputs and seeds. Scoped keep-reset candidate: 102400 ordinary shots, both donor and candidate 1 value error and 0 phase/mask/ancilla errors, mean paid 316130.09541992185, R=1.1967314991687559, DQI cost 306441502849.63837, paired bit diffs [0,0,0,0].
- Joint direct+scope candidate: 4096 ordinary shots 0 errors on both, mean paid 316129.37939453125, provisional sample-size-dependent cost 764295958843.795; NOT comparable to a 102400-shot result. 1024 forced shots: both donor and candidate 488 value, 257 raw phase, 499 union, 0 ancilla/mask errors. Paired diffs all zero. No measured score improvement or decoder repair.
- Strict Lean 4.35 CI 46079405132 passed all eleven scope lemmas (propext for five; six axiom-free; no sorryAx).

## New all-weight shared phase arithmetic, packed coefficients ABI only

Let D be the monic locator, w=deg D<=35, and B(X)=sum e_i*x_i*D(X)/(X-x_i). Then B(x_i)=e_i*x_i*D'(x_i) != 0, hence gcd(B,D)=1. Compute K=D' * B^{-1} mod D. For nonzero x, root test can use Dpad=X^(35-w)*D; at a root e(x)=1/(x*K(x)). Store low 35 coefficients of the monic degree-35 Dpad and 35 coefficients of K (840 qubits). w=0 has Dpad=X^35, K=0. This representation determines the input syndrome on the legal domain. The factor x^{-1} is transported into the classical phase mask. Existing #241 guard4, #237 rank15 and HMR repayment are reused. No separate chart-specific phase scan.

Reproduce: run normalized_scan.py --count 4095 in this directory with KickMix 1.0.0 and numpy. The reference pack(S) starts from moments, not locations; it is a host classical routine ONLY for generating native test inputs. Reversible syndrome-to-packed transform and its inverse are NOT implemented. Therefore the native circuit is not the full DQI oracle.

- 16 points: 874 Q, 123325 instructions, 784 static paid, 72/72 native shots PASS.
- 4095 points: 874 Q, 30313084 instructions, 200655 static paid (49 per point), 72/72 native shots PASS (one legal example for each w=0..35, two independent seeds). Phase, packed input restoration, mask and ancilla verified. 147420 algebra point comparisons against independently generated sparse support, zero errors. KMB SHA256 48850f385df08ed8258b16c3663fa66e7458b0038003f330a8fb83157d873344.
- The current scan has no complete decoder cost or score. Do not subtract 200655 from the original donor without accounting for reversible encoding/decoding and physical allocation.
- NormalizedScan.lean adds three local algebra lemmas; CI 46079662648 launched, not a proof of reversible packing or full tape.

Original and candidate binaries are reproducible via sources, not committed as large binary files. The temporary sandbox is not a persistent artifact store.
