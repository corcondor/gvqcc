# V49: nonlinear phase pullback and private-HMR boundary transport

Research only — NOT SUBMISSION. SHA-pinned V46 integrated parent c8e6813e4fd5b5d56ef8af117d2770d58f3a087bb9e49824845824aea7b8ca15.

| variant | ops | full cuts | expected paid | HMR |
|---|---:|---:|---:|---:|
| V46 integrated |39688|2778|23175/16|1281|
| V49 phase |39514|2777|23175/16|1281|
| zero coin |39521|2767|23183/16|1281|
| presampled |39524|2767|23183/16|1281|
| private HMR |39518|2767|23183/16|1280|

Final native SHA256 5db643cbb52afd1a8104dc914197db7fdf5ce5ac5fd434341f0986ec5dca29b3. Full serialized paired BDD PASS 3,133,452 inputs, 1281 independent source HMR variables; candidate ignores one variable. Data, phase, rotation, guards and final records equal; source private record differs only prior to overwrite. Whole width37Q, 257 full episodes vs258. No official verifier/score, no main/Kaggle change. Lowest E1406.3125 not beaten.

Exact ANF phase pullback across 647 nonlinear gates, 375 windows, 2264 anchors, 1986 degree<=3 and1264 degree<=2 fits, 58 adopted, -174 ops at fixed expected paid. Separate reread PASS. Phase core in this branch, complete native code in archive. Nonlinear coordinate reset: 1178 windows /899 quadratic reset solves, no fit; difference mode 4 fits of same physical interval [22016..22020,22031), four-frame phase dictionary no acceptance; eight data-only bodies retained but not verified native replacements.

Direct target update in phase parent [21958,21969): q36 temporary replaced by CCX24,31,28; seven CZ telescopes and one guarded CCZ. 10 full cuts removed for +1/2 expected paid. Zero coin and presampled versions exact. Extended [21958,21980) source22->26 native operations, no q36 references at all, two original HMR boundaries. Omit source HMR21968 + its immediate phase correction because their total sign cancels, record1 has no other reads before unconditional HMR21979 overwrites it. Exact serialized replay using both original independent variables, no postselection or presampling needed. Source classical record may differ inside interval, not after overwrite.

Finite audit V46: 6687 matrix congruences matched; nonzero-word XOR naive38446, one-level Strassen509453, blocked33672. 1942 exact sparse quadratic Walsh spectra compared against integer FWHT; 471528 dense output points, 4975144 dense additions/subtractions vs14332 sparse coefficient updates; 12691 nonzero outputs. Different representations, no wall-clock or physical gate claim. No OpenAI asymptotic algorithm port. Reviewed math fork 3344da59991ed94f9ba711217b29c1d760badfa6, family379 claims square exponent9/4 (not5/2) and Fourier exponent1/2+o(1) with admissible coefficient fields. The claimed Fourier bound does not directly transfer to GF(2) Walsh; independent batch bound does not imply free cross-instance sharing. Finite block Strassen is not the9/4 algorithm. Reviewed PR106-112 including PR112's node86 214->97 CCX and unresolved node89, distinct diagnostic parents, no arithmetic addition.

References: Amy/Lunderville https://doi.org/10.1145/3704873 (Boolean relation pullback adapted), Amy/Ross https://doi.org/10.1103/PhysRevA.104.052602 (phase-state duality), MBUndo https://arxiv.org/abs/2611.02345 (measurement phase/liveness, not full implementation), PhasePoly https://arxiv.org/abs/2506.20624, https://arxiv.org/abs/2505.09320 (multilevel IR, related survey). Lean local algebraic identities PASS run45609831623; no full Lean circuit proof. No training. 
Companion reproducibility ZIP GVQCC_V49_NonlinearPhaseTransport_NOT_SUBMISSION.zip SHA256 a5b893d3c8a0a74848aea3a2b81f16c1fe241acdb740a26a75b820a910e042dd (313 files). Exact source/candidate native binaries, scripts, receipts, negative tests and manifest in conversation archive.