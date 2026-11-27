# 316K formal-refinement audit (research, not submission)

Pinned donor SHA-256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52, 900Q, 69,782,188 native ops. No replacement of donor.

## Strict Lean
- ProjectivePivot316, 14 audited theorems: strict run 46068944736 at e98ce2711661c33c71b8853bfe773b29592c3b76 SUCCESS. Syntax of omit fixed without weakening statements.
- DQIRefinement316, seven additional theorems: strict run 46069118795 at b9ab2c1af8a36d66a223df84eae0a17924497ad3 SUCCESS. Total 126 audited declarations in this job, no sorryAx or ofReduceBool. Theorems: sparse uniqueness for 70 moments on union of ≤70 nonzero nodes; phase target congruence; exact/necessary HMR repayment; compute-scan-uncompute composition; value and phase counterexample rejection. This is an abstract composition proof, not refinement of the native 69M-instruction tape. CorrectOracle currently requires all classical bits restored, stronger than the public mask restoration requirement; refine to projection at the physical ABI before claiming equivalence.

## Full native counterexample
New fixed circuit KickMix 1.0.0 regression: 64 distinct legal inputs (8 each weight 0,1,2,6,17,18,31,35), two seeds 60201 and 60202. 64/128 value errors, 41/128 raw phase errors, union 74/128; dirty/mask zero. No external chart selection.

Simplest witness: one nonzero error at position 0 of magnitude 1, all 70 input syndrome words 1, all classical masks zero. Expected output same 70 words and phase +1. Independent C++ KMB replay through all 69,782,188 instructions with every HMR outcome zero: 64 legal weight-one cases, 64 value failures, zero phase/dirty/mask failures. For the simplest witness S0 changes from 1 to 2865. Independent KickMix seed 60203, 16 copies of this witness, all 16 value failures and 13 raw phase failures, zero dirty/mask errors. Complete output vector identical to the independent zero-HMR replay in every shot. The universal correctness proposition for this exact original binary is therefore false. This is native and independent replay evidence; the C++ interpreter/trace is not kernel-certified.

## Native arithmetic proof audit (exact finite Boolean checking, not Lean certificate)
- GF12 inverse XOR primitive from Opt.invxor: 33Q, 1878 ops, 392 static paid. SHA256 28a99468a439d38ea42e377e517e309659377798b51bffc4e7e4391c87e8f2a3. Complete 4096-entry truth tables for each input bit; affine symbolic coefficients in all 12 arbitrary dirty target bits. All 186 HMR pairs individually proved by exact equality of measured bit and current control product, independent of the measurement outcome; all aux zero. Covers 4096^2 input pairs.
- GF12 product XOR 42-CCX: 36Q, 510 ops. SHA256 2e41255074ec51f4c5ac281cd32e0c752a4ac11018705a1c3c55ebef791f956d. Exact Boolean ANF on all 36 input/dirty target variables, every coefficient equal to the multiplication tensor; input preserved. Covers 4096^3 tuples.
- Exact structural-expression HMR audit of previous all-axes 897Q KMBs: forward 888/944 HMR witnesses proven syntactically, 56 inconclusive; reverse 889/944 proven, 55 inconclusive. 37/57 and 36/57 scratch outputs structurally zero, other ones not simplified. These are not error counts and not a complete proof. Need semantic macro certificates for field inverse/product cleanup, then connect native physical seam, projective log packing, scan phase, inverse extraction and public mask projection.

Full standalone audit sources, KMBs and native receipts in conversation artifact GVQCC_316K_Formal_Refinement_Audit.zip. No new repaired full DQI circuit, universal physical proof, cost/width improvement, main merge or submission claimed.
