# Low-width shared angle dictionary — research only, NOT SUBMISSION

Hard maximum width 36. New native circuits are generated from the V52 analytic spectral plan and 34Q serialization template, not the former incumbent.

| Q | CCX | arbitrary rotations | ops | HMR | SHA256 |
|---:|---:|---:|---:|---:|---|
|36|17051|7050|200989|6991|15a44966ba3034a88e703993d89fc625c8d09ed312e9262ff67b521ecb395c7d|
|34|21820|5399|258639|5340|63b11abe5df0e59a01c0ddce2020d1b5f93656106518125e26e03339996ebd12|
|32|21591|5573|254083|5514|e09c3e24eb35a54be3e3d8e328bddf7742c847e454e7d6b12d5340597dd2524a|

All native bytes were independently reread, with the maximum wire index 35/33/31 respectively. Full 2^22 input cube control equality, independent HMR phase cancellation, scratch restoration, and integer phase contraction PASS. All 3,133,452 legal inputs satisfy exact squared relative tolerance; worst ratio 0.8125815968960524. Relative precision alone is not official acceptance. No official verifier/rotation synthesis or score improvement is claimed.

## Construction
For mutually exclusive prefix predicates f_i, the controls f_i p_i are mutually exclusive, so the sum of their equal-angle phase terms is exactly a times their XOR. Retain a small cluster of prefix flags; compute the common predicate onto one carrier, rotate, HMR-reset the carrier, and cancel the sign debt by classical-outcome-controlled Z/CZ on the prefix flags and affine parities. Optimize the angle dictionary by replacing a with b+c mod 2^64, or signed power-of-two sums; each angle needs max_i multiplicity_i layers in a disjoint cluster. Search trades off this layer count and CCX occurrence count. At 34Q, grouping alone has 7,459 rotations; 1,466 accepted exchanges give 5,399. At 32Q, grouping alone has 7,636 rotations; 1,455 exchanges give 5,573. The exchanges preserve exactly the rounded spectral specification, not the unrounded one.

Full native code, template34.kmb, KMBs, tags, exact replay, receipts, cluster logs and SHA manifest: companion conversation artifact GVQCC_Sub36_AngleDictionary_NOT_SUBMISSION.zip. This PR records the results and mathematical identity; it does not upload the binary archive. Reproduce using QWIDTH=32 or 34 python angle_dictionary.py template34.kmb OUTPUT.kmb. Main/Kaggle unchanged.

Separate analytic experiment: 12,376 dyadic piecewise affine blocks, worst error/tolerance 0.7010504603. No native circuit or gate-cost claim for that experiment. Next priority is eliminating costly repeated controls and reducing the angle dictionary by orders of magnitude, without relaxing the width bound.
