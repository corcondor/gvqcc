# GVQCC exact audit: nonlinear cache and 37Q width — 2026-11-23

**NO SCORE INCREASE; NO NEW KMB; NO NATIVE KICKMIX VERIFICATION.** Baseline public Goodpjw V8: 33.13521306472748.

A newly executed source-level 15-bank ANGLE audit modeled all 2^11 address inputs, conservatively taint-tracked dirty word inputs, and compared the control-product truth vectors in the pre-first-HMR classical prefix of each untouched KMB. For the target pattern **cache one repeated CCX product in a formerly unused clean qubit and substitute CX**, no repeated product in the proved dirty-independent subset was available (0 savings). All untainted nonzero products were GF(2)-independent over these 2048 addresses, e.g. bank0 109/109 and the 76/76/81/81 covered subsets of other banks. This says nothing about broader global nonlinear tensor resynthesis.

Separately, an exact HMR=0 trajectory of the public **37Q inverse sqrt** was simulated on 2048 valid input addresses, with an explicit 37-input witness of GF(2) rank 37 at operation 1863. The witness was rechecked by an independent C++ simulator against all 37 qubit-state bits, then Gaussian elimination found rank 37. Hence a **purely affine reversible width-36 encoding of that exact reachable intermediate state cannot work**; a nonlinear schedule or state recomputation remains possible.

A C++ three-valued static analysis on the original 900Q / 69,782,188-operation DQI KMB identified no provably constant-zero/constant-one CCX controls under this conservative abstraction. This is not a global impossibility proof.

Reproducible execution ZIP in the 2026-11-23 conversation:
`GVQCC_20261123_Exact_Width_And_Cache_Audit_NO_SCORE_UPDATE.zip`, SHA-256 `3f93f5ffc30f666c2f339c8c6baa346ea4f2d1abccc9682562ccda52d1f39d28`; includes source 15 ANGLE KMBs, inverse-sqrt 37Q KMB, Python/C++ replay, 37x37 witness, SHA ledger. DQI original 617MB KMB is not duplicated.

**Next successful move must be an actually cheaper generated KMB, not a witness or an explanatory proxy, and then native KickMix pass and score.** Main untouched.