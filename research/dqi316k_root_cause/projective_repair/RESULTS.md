# Total projective Hermite chart, 316K research only

Pinned donor SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52, 900Q, 69,782,188 ops, 318,972 static paid. No other donor substituted.

## Counterexample to the three-choice fix
Construct 32 legal base syndromes (weights 6,10,14,17, eight each) with six GF4096 constraints on the first two Hermite-node jets. Choose u1=0 for scale1; for scale2 choose nonzero u2 and v2=b2*u2/conj(u2); for scale3 solve backwards f_next=(1/f+h)/g to force slot2. Exact classical first failing slot 0,1,2 for scales 1,2,3. All 64 native zero-mask shots for each scale have restoration errors, raw phase errors 35/29/25; no dirty/mask errors. Scale4 selected by external all-chart screen 64/64 clean. NOT coherent selector or official cost.

## Native total residue and polynomial chart
T(n,d)=(n,d/n) on nonzero pairs, otherwise swap. Inverse T^-1(p,h)=(p,h*p) on nonzero pairs, otherwise swap. For d!=0, h=0 precisely marks n=0; when d=0 and n!=0 use p=0 sentinel. Both-zero is outside the coprime polynomial domain, but local permutation is still reversible. For regular p,h, D_q += h*N_q + quotient(h*n,g) in characteristic two, with g monic quadratic. For either zero axis, omit the shear. Keep both residue slots until the orientation is encoded in subsequent physical storage. A single zero quotient sentinel after discarding an axis is not enough.

| actual local native KMB | Q | static paid | ops | shots each direction | errors |
|---|---:|---:|---:|---:|---:|
| residue pivot |112 (48+64)|3618|15397|18432|0|
| optimized HMR/affine transposition GF64 inverse |105 (48+57)|2318|16217|18432|0|
| polynomial chart unit denominator |897 (840+57)|5048|49523|1280|0|
| both singular axes |897 (840+57)|5118|49827|2048|0|

AllAxes forward SHA256 553253cf80f797742b5e60e0a7ca536a11e8b0885e719e8827297d896c2232f8, reverse abfbd8ffe2a003cab6e53fabb64259798771ef69aef04f2d360e1709f2b8ac69. Each 1024 distinct contexts, two independent KickMix seeds. No physical donor splice, no full 897Q DQI.

## Classical all-chart reference and phase
Initial rational pair from existing 35x35 Hankel solver, no known weight supplied. Reduce larger polynomial when both residues nonzero, or whichever residue is zero; preserve Bezout witness. Potential floor((len N+len D)/2) decreases by >=1 at each degree-scheduled step, even in tied-degree case. Initial <=35. Exact reverse, support/magnitude recovery and phase checked on 1337 legal inputs, 754 supplied-mask comparisons, max 35 stages. Projective continuants evaluated directly from log reproduce magnitudes without terminal scalar; max 70 field quotient words+35 orientation bits=875 bits before length metadata. Thus no compact 840-bit log or full native circuit established. Repeating independent 5118-paid steps 35 times in each direction is too expensive; reuse donor arithmetic and solve orientation storage.

## Physical seam audit
Independent bit-sliced 2048 input snapshots, zero masks/draws, at source operations 19992090,37473549,42450257. No affine GF2 map from raw quantum state to either target tag bit fits the first 1024 inputs at these three seams. Also no fits for sampled canonical locator/magnitude bits. This rejects direct affine recovery at these cuts, not every possible nonlinear decoder or seam.

Lean: InvariantPad strict CI at 8979525 succeeded run 46067648075; ProjectivePivot316 first seven lemmas elaborated without forbidden axioms but strict job failed on two unused-instance lints, corrected. Expanded 14-lemma run 46068567752 must be checked. Full source, receipts and emitted native local KMBs in conversation archive GVQCC_316K_Projective_AllAxes_897Q_RESEARCH.zip. No whole-circuit proof, official score, main merge or Kaggle submission.
