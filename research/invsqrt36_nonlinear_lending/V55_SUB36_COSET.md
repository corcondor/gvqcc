# V55: hard sub-37Q whole-oracle synthesis
Research only — NOT SUBMISSION. No modification to main or Kaggle; no official verifier or score claim. We have not displaced the competitive 37Q incumbent. Every new verified circuit has physical width at most 36. Parent PR124; PR125 is a distinct approximate plan and uses shared translations, not signed coefficient-space cosets. PR121 low-rotation permutation construction is prohibitively expensive; PR123's dyadic polynomial audit did not emit its low-width evaluator. Do not repeat 37Q local-cut searches.

## Native full-oracle receipts
| Q | ops | CCX | generic rotations | HMR |
|---:|---:|---:|---:|---:|
|25 (unitary)|89708|10806|9042|0|
|25|94437|8484|8549|2804|
|27|90069|5131|8549|2841|
|29|89277|4485|8549|2843|
|32|88283|3680|8549|2846|
|35|87821|3371|8549|2849|
|36 affine lookup|991232|432814|727|0|
|34 quadratic lookup|337743|169576|6680|0|

All 8 KMB candidates independently serialized, checked on 4,194,304 inputs, restoration, phase and exact squared tolerance on all 3,133,452 legal inputs. All adaptive coset plans have max error/tolerance .8489570934325457; each measured flag equals the product of actual current controls and both possible outcomes cancel via guarded Z/CZ, no postselection. The unitary 25Q candidate has ratio .843884686. 35Q SHA 37b78f479eb690b0c3c6aa9149b7d0308e4cd6057e63a1a86350f913e3adae2f. The 35Q circuit was re-emitted byte-identically using a verified 25Q format template, no 37Q input circuit needed.

## New search
12,861 Fourier coefficients of 56 dyadic blocks (V54 plan_0), regrouped by equal absolute coefficients and character signs into 7,844 signed affine cosets. Adaptive nearest-magnitude/bin quantization within exact 85% tolerance budget: 3,884 trials, 37/56 blocks improved, 7,427 groups. No training. Identity: sum_(v in V) c eta(v) chi_(s+v)(x) = 2^dim(V) c chi_s(x) product_j [chi_dj(x)=eta(d_j)]. Shared prefix trie; exact signed parity translation with aggregated unconditional compensation. This changes the approximate phase, rather than preserving the PR125 phase. Different from prior direction sweeps; no asymptotic OpenAI algorithm port.

## Arithmetic alternatives, rejected on cost
Affine fit with 10,907 dyadic blocks, shared vector-valued lookup, 36Q and 727 generic rotations, but 432,814 CCX. Exact tolerance max ratio .7999820951. Full replay split into contiguous op ranges [0,623127), [623127,991232), rotation ranges [0,35), [35,734). Initial verifier timed out; receipt rotation-index shadowing corrected. Independent coverage audit includes all coefficient bits, 207,635 leaf polynomial checks. Quadratic fit 1,007 blocks, 34Q, 169,576 CCX, 6,680 generic rotations, 35,684 leaf polynomial checks; 36Q quadratic exploratory emission not independently verified and excluded. Haar bit-plane inspection was only diagnostic; switched to shared affine/polynomial lookup and cosets because of leaf cost. These are not competitive candidates and should not be repeated unchanged.

## Reproduction
Companion GVQCC_V55_Sub36_Coset_NOT_SUBMISSION.zip (66 files; SHA256 d0499c4db2eedc9d543a5e18378a959b7097d519c9eb9d083952a7c220c978f3), delivered in the research conversation. Includes all verified KMBs, native code, source plan, signed coset plan, full-cube verifiers, per-circuit receipts, SHA manifest, 25Q template, instructions. Compact exact coset core in this PR. Lean local identities do not constitute a proof of the full KMB or official score. Remaining task: a low-rotation structured arithmetic evaluator (roughly incumbent 33 generic rotations) with economical coefficient evaluation in <=36Q; high-rotation diagnostics are not acceptance.
