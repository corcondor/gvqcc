# Reusing the historical Vandermonde guard and central transport (NOT SUBMISSION)

No new mathematical framework. This is a native implementation of the existing PR #209 supplied-monic-P17 and 52-moment guard. Its mathematics comes from [#209 AffinePadding](https://github.com/corcondor/gvqcc/blob/3c3ed573c995d280a2dc54b20b5e0c6a9644824b/research/dqi_cutoff18_strict/AffinePadding.lean) (moments_injective, low_degree_obstruction, moments52_injective), [#213 TransposeTransfer](https://github.com/corcondor/gvqcc/blob/4218534c2ce88a6d9b5533c31ffd01a628bf623f/research/dqi_cutoff18_strict/TransposeTransfer.lean), [#77 V29SharedFrame](https://github.com/corcondor/gvqcc/blob/93cc08e5eaeb8dffe005273b4855717c2f583a3e/research/invsqrt36_nonlinear_lending/lean/V29SharedFrame.lean), PR #5 parity transport, #93 Abel/central syndrome hubs, #187/#190 exact 42-CCX multiplier, #213 GF64 thickening and #215 temporary AND. PR #166 and #168 had no DQI paid improvement; do not relabel those as a new score.

On distinct nonzero locators x_i with nonzero e_i, the 35 recurrence residuals are R_k=sum_i e_i*x_i*P(x_i)*x_i^k, k=0..34. Vandermonde injectivity for w<=35 proves R=0 iff P vanishes on all locators. A monic degree17 P cannot vanish on 18 distinct points. For a correct low-weight monic padded locator this test accepts. For an arbitrary P this is a recurrence checker, NOT a syndrome-only low-weight classifier: it can reject a wrong P even on a low-weight input. A syndrome-to-P generator (or the same physical live P) is still required.

For triangular cross block low A, high B, coefficients C, reverse the low word index. The coefficient tensor is T_ijk=[k=i+|A|-1-j]. Evaluating the low block and the dual output block on |A|+|B|-1 Vandermonde points yields the middle product by transposition. Dynamic partitioning chooses the cheapest of the three axis orientations and direct products; all selected coefficients are checked. The GF64-thickening planner is the unchanged archived upstream code (ThemBones milestone generators v2; retain Apache-2.0 LICENSE/NOTICE and upstream credits). Its binary transposition uses the nonsingular GF4096 trace pairing, with full bit-basis-pair equality checked on each selected block. No approximation or error-tolerant acceptance.

## Native measured results

|variant|Q|static paid|ops|native forward+guard checks|
|---|---:|---:|---:|---:|
|#209 old joint guard|876|17968|829789|1060 guard (historic)|
|transpose guard|876|15784|785577|1060 guard +1060 prefix|
|tower guard|875|14321|2740179|1060 guard +1060 prefix|
|central guard|875|14321|1630899|1060 guard +1060 prefix|

All new checks zero value/phase/workspace errors. Same 530 input rows twice per circuit: 466 structured legal-syndrome/candidate rows and 64 arbitrary P,S rows, including Vandermonde leading-zero adversarial inputs. Reused old guard target ABI (829 data including target). Central route reduces tower instruction count 1,109,280 at equal paid/Q; it is not fewer instructions than the original #209 guard. Prefix paid 8568 ->7476 ->6765. Central full guard checks 3176 field coefficients and 249696 binary tensor input pairs, with repeats across forward/reverse blocks. No new Lean claim: the cited historical laws are reused; emitted tape semantics are tested separately.

## Reproduction

Extract the prior user-owned archive GVQCC_316k_AFFINE_CHART_REPAIR_RESEARCH.zip for recurrence_guard.py, direct_codec.py, transport42_lean.py, zero_mask_weight_audit.json. These were the exact inputs (SHA256 below); no requirement for a new copy of the original 316k binary. From the restored #218 archive use third_party/thembones-milestone-generators-v2/dqi/kit/kv_unfused5/exp/new/a03 as GVQCC_TENSOR64_DIR; the tensor64.py import requires that kit's original decoder directory hierarchy. Use KickMix 1.0.0 and NumPy. Put these three patch scripts beside the base guard and run:
```sh
python make_transpose.py
python make_tower.py
python make_central.py
python transpose_guard.py
python tower_guard.py
python central_guard.py
```
All three scripts were executed locally; KMBs and receipts are also in the companion reproduction ZIP.

Base hashes:
- recurrence_guard.py 62ab7f80e98e0133ff0e7d24097ed954fbf5f6b9f9e7e47a3e2f5a8ffae19608
- direct_codec.py 2c897def5c2c5e8e29e579d45663e9741b46ad2482ea399ddb28e9d3ecf82094
- transport42_lean.py 4397c09341892e7af843471b5e3e1fc0b429512f895b9674050551c6497c1ade
- zero_mask_weight_audit.json 4443c0ff154025c9170b7f0f1a2fd581c8324293f6a4d4da1abdc1ab59529902
- tensor64.py e20add6c14b4d6338faa29abb0b6fca3d6310d76652732019fa9e8db659b59c3
- field.py d1346ff195b02fabfda21904094410291aac6fc08e0c182a1b639c14ab743274

No all-domain physical refinement theorem, no full 316k repair, no 896Q integration or score. Known arithmetic restoration errors remain. Use the lower-cost existing guard only when its physical input ABI and uncomputation contract are met. Main untouched, no submission.
