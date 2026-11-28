# Public-kit CF integration — measured native results (2026-11-27)

**Research only; not the owner's private 344k build or an official score. Do not submit or merge.**

Pinned upstream commit `a9effc375527bf0b6962c178530d353eb70a3fcb`. Source archive from [Actions artifact 15204231284](https://github.com/corcondor/gvqcc/actions/runs/46010445718/artifacts/15204231284), successfully downloaded and extracted. Tar SHA256 `e6347dcb03c8998cc070e77f13bb82f811dae6d6c98e19b809f21597e1055e8b`.

Local KickMix 1.0.0, Python 3.13, same 256 synthetic monic inputs (32 random, 32 each of seven degree-3 drops). Actual converter build via upstream `dqi_int_convtest` and the complete public kit loader. Both PDR directions enabled, blocks 15,13,11, share/liveB/local enabled.

| Variant | Q | Forward ops | Forward mean paid | Round ops | Round mean paid |
|---|---:|---:|---:|---:|---:|
| Unpaired public baseline | 886 | 5646873 | 61778 | 11424426 | 124750.8359375 |
| Documented CF repair + PR187 lower/CG fusion | 886 | 5519646 | 60948.921875 | 11128347 | 123310.375 |

Every forward A/B word agrees on 256/256 inputs, all 256 round trips restore inputs and ancillas with zero phase errors in both variants. Roundtrip KMB SHA256 `f5d1d8792b736198d3eb92a509336b0c8c9e8288d9090b9df9e368b87ec4b397`. Forward stage's intentional nonzero workspace and deferred phase are not classified as failures. The 1440.4609375 saving is versus unpaired public baseline, not the private 122847 / 123440 pair.

## Actual route helpers, three overlapping contexts

Actual upstream `route_block_T`, `flag_and`, `erase_flag_and`, `masked_word`, `erase_masked_word`, and `mul_xor0`, no mocked measurement helper. Three route blocks U=15,13,11, two payload words per level. Tests: 2048 inputs × 2 measurement seeds, all 256 assignments to eight supplied consistent gap flags, random field words and dirty targets. Independently computed route expression. Not a whole converter or a proof that the documented CF law covers all decoder inputs.

| Variant | Q | Paid | Ops |
|---|---:|---:|---:|
| Upstream without CF | 458 | 750 | 16740 |
| CF literal correction | 458 | 1125 | 25074 |
| CF fused route | 458 | 969 | 24888 |
| CF fused + PR190 510-op multiplier | 458 | 969 | 9984 |

All 4 variants: zero value/phase/ancilla errors relative to each variant's stated route specification. The unfixed variant is not a correct decoder. New fused510 tape SHA256 `05787974ea906bc32b7aab401905f84b0a09f6a523b3392042ea4d10d6fa45d3`. See PR190 Lean proof [46010303030](https://github.com/corcondor/gvqcc/actions/runs/46010303030), 42 CCX, 510 ops, exact all-input symbolic multiplication, no sorryAx.

## Missing private materials

The upstream record `record/best_q31zc14_repro901_zd20.txt` contains the 29-extension recipe and reports 901Q, about 343998 mean paid, one value error on each of two official salts for file A. It is not a zero-error candidate. Several older build patches (t1/r4jt/r4k/r5w), pinvar wrappers, cache/tensor placement specifications and the owner's local repaired PDRFIX_CF are absent. Exact 344k reproduction and same-parent 593 absorption cannot be asserted. Need original repair source and full build snapshot or a complete native repaired compressed binary with layout and manifest. Do not splice the converter KMB directly into an unknown physical layout.

Full public-kit build and unchanged verifier smoke gate are configured in [46010226142](https://github.com/corcondor/gvqcc/actions/runs/46010226142). Converter comparison step completed; full oracle/verifier status must be read from that run, not assumed. No main merge / Kaggle submission.
