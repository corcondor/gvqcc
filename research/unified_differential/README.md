# Discrete differential transport across all GVQCC tasks — research only

Parent V74 whole-task and V71 spectral archives recovered from the user's library. See PR #5, #12, #13, #20, #123, #157, #162 and #164. Do not treat old 46Q textual baselines as new competitive candidates. The KMX experiment in this branch and the native KMB experiment are separate.

| Native KMB | Width | Instructions | Static CCX |
|---|---:|---:|---:|
| invsqrt V74 |25|62079 -> 61260|5116 -> 5007|
| invsqrt V71 |36|52545 -> 50906|1358 unchanged|
| DQI V74 (two passes)|900|69577739 -> 68820952 -> 68799061|312234 unchanged|
| DFTHC-SOS 15 loaders|128|371111 -> 369838|3357 per pass unchanged|

The compiler transports an elementary nonlinear shear T(x)=x+w p(x) through F(x)=Ax+b using F T F^-1(y)=y+Aw p(F^-1(y)). Common direction and intersecting factor planes allow two quadratic products to fuse, up to a linear correction in the Boolean ring. Exact sparse square-free ANF verification of each accepted pair; full affine-matrix equality for every accepted affine block. No width increase, HMR order or rotation angle change. Boundaries: same classical guard, <=512 instructions between paired CCX; <=256 instructions and <=64 active wires per affine block. 109 paid fusions on 25Q. Phase extension investigated 660 pairs, no accepted cubic fusions. Full DQI second pass repeated affine/CCX compiler only; byte identical to phase extension output.

Independent native replay: both spectral invsqrt circuits all 2^22 inputs, legal 3133452, 2711/1259 independent HMR coefficients respectively; modular 128-bit phase, exact tolerance and restoration pass. DQI 256 arbitrary paired inputs/measurement histories, output, relative phase, classical records, exact per-wire scratch and per-shot paid counts match; this is not official verification. Chemistry all 36570 forward/reverse transitions, 3086 independent HMR coefficients pass; NPZ byte unchanged; no full physical official verification. The model of per-output mixed bilinear rank cost on all 15 ANGLE deltas improves 4170 -> 3865, worse than actual 3357 so not adopted.

Full 104812485-byte reproducibility archive is delivered to the user in ChatGPT, SHA256 5c78cbacd548b7f6830abf4bf1b10cb5c05dee91accc2118f041352188cf2dce. It contains native C++ source, KMBs, independent verification logs, receipts, local Lean source, and NOTICE/LICENSE. Repository snapshot contains portable KMX compiler, local laws, and results; large archive is not uploaded to GitHub. No main merge, official verifier, official score, Kaggle upload or competitive improvement claimed. 25Q/36Q spectral oracles have 7777/7850 generic rotations. Formula cost 25Q improves 1698370.489146 -> 1695645.489146; 36Q unchanged 2332126.562226. Competitive 33-rotation low-width synthesis remains unsolved.

## Related literature and scope
* Amy & Lunderville, POPL 2025, https://doi.org/10.1145/3704873
* Meuli et al., Xor-And-Inverter Graphs for Quantum Compilation, https://doi.org/10.1038/s41534-021-00514-y
* Patel, Markov, Hayes, https://arxiv.org/abs/quant-ph/0302002
* Amy, Azimzadeh, Mosca, https://arxiv.org/abs/1712.01859
* Gidney, https://doi.org/10.22331/q-2018-06-18-74
* Khattar & Gidney, https://doi.org/10.22331/q-2025-05-21-1752
* Paradis et al., Reqomp, https://doi.org/10.22331/q-2024-02-19-1258
* Khoruzhii et al., https://arxiv.org/abs/2602.15285
* Faster Algorithms for Structured Matrix Multiplication via Flip Graph Search, https://doi.org/10.1145/3815436.3815455
* Nam et al., https://doi.org/10.1038/s41534-018-0072-4
* Shirobokov et al., https://arxiv.org/abs/2611.09822

These are sources of methods and design context, not claims of full algorithm ports. Lean source is local Boolean identities only, not compiled here.
