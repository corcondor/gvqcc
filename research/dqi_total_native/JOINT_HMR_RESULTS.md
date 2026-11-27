# Joint mathematical resynthesis of the correct #252 full circuit

Research only, not a submission. Base exact #252 SHA256 a025a17e88e114e7d2971ca3e5f7853d5a6c06faf89f7c2bb3a7651458786be1. All candidates preserve its complete raw-syndrome ABI, 900Q and single coherent circuit.

Actual Vercel native session sbx_ZECaKDm8gpH8zeNjESO5JLIczZFz, pinned upstream dataset v2 runtime. All 912 matched stratified/adversarial executions pass value, mask, ancilla and raw phase checks for each of three successors.

| stage | static paid | mean on matched 912 | instructions |
|---|---:|---:|---:|
| #252 |13207902|13207902|92253336|
| joint_hmr_patch |8601183|8292490.221491228|106659416|
| + factor_guard_patch |6496379|6496379|98249480|
| + shared_factor_patch |6117683|6117683|96911344|

Final SHA256 a5a74c25317c59ebfdee08348668e58088734466e4f9cad4c7aa075d675158e5.
Native full-circuit verification cmd_2ca01c57c1fd42fab0e4697d9731, 912/912.
Additional independent ordinary distribution cmd_5d2de4e99d9d4c0ba1660d277085, 1024/1024, same mean 6117683; all four error counters zero. This is not the unmodified official verifier or private-salt verification.
Final stage counts: decoder prefix 2872519 paid; common 4095-point scan 372645; inverse decoder 2872519. No local gate search is used. The new algebra is applied to the entire native tape.

## Identities
- Exact rank42 GF4096 tensor recovery by affine/ANF propagation, all 144 basis pairs checked; GF64 rank15 via five evaluations over GF4, all 36 pairs checked.
- After computing y*p into work and exchanging under coherent flag f, measured work equals y_after * (p + f*(p+q)), q=p^-1 for f=1. Select the factor once per whole group of coefficients and repay every measured word by transposed bilinear phase. Masked products similarly use a shared f*a and HMR with exact quadratic debt. No measurement of the input or history.
- Unit-series factorization in F[X]/(X^n): extract factors 1+a_l X^l in increasing l; multiply their inverses in decreasing l. In characteristic two the diagonal correction is a_l^2 and is a linear Frobenius map. Coherent boundary guards are incrementally updated only when the suffix has exactly one active endpoint; general pack guards are retained.
- At every scan point, use trace-dual mask u and quadratic tower: Tr_12(u/d) = Tr_6((u0*d1+u1*d0)/Norm(d)); apply again in GF8. Root predicate and every norm/product scratch are repaid via HMR. All 4095 nonzero points are scanned.

## Reproduction
Start from #252 untouched total.cpp.in, build.py and finalize.py; run the three patches in order, then build.py, compile total.cpp with C++17 and generate full KMB, finalize.py, verify.py and distribution_replay.py. The third patch includes corrected max used classical index 49980. The initial native writer generated a file with an oversized header; correcting it and rerunning produced the final hash above. Verification script scope label has been corrected from inherited "no HMR" to "HMR with exact repayment". The native runtime is the pinned public source runtime, not a new official verifier.

## Cross-check of existing cheaper complete line
Independently reproduced #249 on Vercel at identical SHA256 4172a26e1bc065904c56faf113701d7bc04844578863adbbde2f6285735915fd: 899Q, 473009 static paid, 42566825 instructions. Same 912-case #252 panel 912/912 clean, measured mean 399078.03289473685 on that panel (previous ordinary distribution mean 414215.373046875). This is an existing weighted Bezout alternative, NOT a new cost reduction from its own baseline, and not substituted for #252. It is a much more promising competitive backend than the high-cost variable-degree CF rebuild.
Old saved 622 panel native replay not completed; whole-circuit Lean proof and unchanged official verifier not completed. JointHMR.lean contains algebraic lemmas, not yet checked in Lean CI. No score improvement, main merge, or Kaggle submission claimed.
