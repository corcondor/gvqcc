# Independently paired ranking of three complete 18-file review archives

No Kaggle submission or official score. The 102,400 ordinary shots used one
common distribution sample and one common independent AVX512 HMR stream.
The 622 saved stress inputs used actual KickMix 1.0.0 with identical seeds across
tapes. Do not treat those selected stress cases as an IID estimate.

| Archive | DQI mean paid, common ordinary | ordinary errors | stress value / phase-only / union | conditional overall score |
|---|---:|---:|---:|---:|
| 292×294 | 316124.943555 | 0 | 407 / 3 / 410 | 33.33564017 |
| #306 (299 Joint + V111 Chemistry + V112 InvSqrt) | 316124.943555 | 0 | 407 / 3 / 410 | 33.34249384 |
| 8-anchor + #299 Joint + commuted V112 Chemistry + V110 InvSqrt | 316119.025469 | 0 | 407 / 3 / 410 | 33.34270191 |

#294 and #299 have byte-identical per-batch ordinary CSVs across all 200 batches
and identical per-case failure flags in archive. #299's reduction is static
(CCX 311463→311202, CCZ 6716→6686, CSWAP unchanged at 108). It does not change
the observed executed cost. #306 wins vs. the previously delivered bundle
predominantly because Chemistry's paid/pass falls from about 3266.5 to 3262.5.
V110/V112 inverse-square-root have distinct files, but the exact weighted
expected paid is 11237/8 for both per the #306 BDD receipt. The original #292
inv-sqrt cost uses its matching older two-salt receipt, not a transplant.

The 8-anchor tape's paired savings are 606012 paid in 102400 shots (5.918086/shot).
Static CCX/CCZ/CSWAP are unchanged vs #299. On the stress archive it has exactly
the same per-case union, restoration, mask and dirty flags. Raw phase flags
change only among already-bad cases (20 clear, 15 appear). This does not repair
the stress defect and is not a private-salt guarantee. DQI tape increases from
87,704,819 to 158,899,695 instructions and the complete compressed archive is
252,170,930 bytes. No Kaggle runtime or upload-limit claim. Best conditional
score of these three is 8-anchor; #306 is the smaller review alternative.
The estimate to reach 33.36 needs about 491.5 more paid/shot at fixed 900Q and
error factor. A single ordinary error has a much larger effect than this
score difference between #306 and 8-anchor.

## Reproduce

Release source archive `GVQCC_Integrated_33_3427_SOURCE_RECEIPTS.zip` supplies
`other/src/{make512.py,direct_codec.py,native.hpp,replay512_noraw.cpp}`. Delete
the historical /tmp import path in make512.py (use its same-directory
direct_codec.py). The earlier reference archive `GVQCC_316K_RANK15_FULL_SPLICE_SOURCE_RECEIPTS.zip`
supplies `joint_work/audit/saved.bin`. The #306 audit archive supplies
`audit/integrated_manifest.json`. Use Python 3.12 + NumPy + pinned KickMix
1.0.0 + recovered official DQI verifier, and an AVX512-VPOPCNTDQ CPU. Original
filenames, SHA256 hashes and member hashes are in paired_receipt.json. Copy
each DQI member as d294.kmb, d299.kmb and d8.kmb respectively. Use zipcheck.py
with the #306 and 8-anchor manifests to recover zip306.json and zip8.json; the
delivered old 18-member archive's hash list is recorded as the 294 archive
entry. Run run_pair.sh. Retain per-case flags only locally; published
paired_receipt.json contains aggregate counts, not private inputs.

Upstream: https://github.com/corcondor/gvqcc/pull/292 and
https://github.com/corcondor/gvqcc/pull/306. #301's raw-moment phase alternative
does not enter any of these tapes. No component CCX saving is credited unless
it is present in the complete tape.
