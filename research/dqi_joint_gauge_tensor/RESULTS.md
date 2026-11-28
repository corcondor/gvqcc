# PR294 native joint DQI result (research only)

Exact parent: #293 SHA256 df3dac81eec66712d3d1bc57751c85e1f2c09cd09431a2b1b2a3eed00df2c255.
Exact-two donor #292: c70ff4cd3f767394bd428738fc453fbd4509e6c762c6585c0b48758cf8b976b4.
Joint candidate: b9f72a7bde001b81e0dc2530618dfa29815038b0bec7a542f75b2e3298d26870 (canonical KickMix reserialization SHA confirmed).
Scale2-only: a5ed693688a2f08a78f4f7625f6efc899df9074c46e1ca10d0c040abe8b55651.
The splice checks register descriptors, identical 840 quantum prefix gates, and 4096 matching instructions after the classical gauge boundary; this is not a whole-circuit proof.

| Metric | #293 | Joint |
|---|---:|---:|
| Q | 900 | 900 |
| Static CCX | 311463 | 311463 |
| Static CCZ | 6716 | 6716 |
| Static CSWAP | 108 | 108 |
| Static Toffoli-like | 318287 | 318287 |
| Ops | 66735441 | 87702020 |
| Ordinary matched 8192 mean paid | 316144.56481933594 | 316139.33740234375 |
| Ordinary matched 8192 errors | 0 | 0 |
| Stress union errors, 1440 | 149 | 141 |
| Stress value errors | 144 | 136 |
| Stress raw phase errors | 78 | 71 |

On matched 2048 ordinary shots the mean executed CCX is 309416.12744140625 -> 309411.22998046875, CCZ 6603.375 -> 6602.88525390625, CSWAP 108 unchanged.
Scale2-only stress raw phase 70, value 136, union 141. All 136 constructed weight 1..17 cases still fail. No claim of complete decoder repair.

Completed independent public-reference KickMix 1.0.0 streaming replay: 102400/102400, empty salt, batch 1024, all four error counters zero. Mean paid 316123.7566015625; upper effective error bound 0.0008660587301657926; reference-formula cost 305034443914.0005. This is not unmodified CLI (default batch 256) or private-salt verification. Different input seeds mean this independent average is not a matched cost comparison.

Negative passes: 302471 affine paid pairs, 300466 phase-bridge pairs, dense GF2 span/measurement tests, 50719 fixed product blocks with 311096 CCX, wider inactive guard test and guarded diagonal collection yielded no further static paid reduction. No global optimality claim. Local six-input D16 polar spaces from #278 source have ranks 4/5 and no nonzero decomposable polar; separated quadratic-product lower bounds 5/6, independently checked across 70 source groups. Not a whole-circuit lower bound. The two canonical spans and Plucker identity are Lean-checked. Strict CI run 46133518541: 17 declarations, 11 axiom-free, 6 depend only on propext, no sorryAx or ofReduceBool. Full native source and matched fixtures are in companion archive.

No merge to main or Kaggle submission. Longer classical prefix trades instructions for small expected paid savings.