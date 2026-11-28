# Exact complete-tape integration (diagnostic only)

Pinned input uncompressed SHA256: 54817e9385f24940585f5a391025152d4a65a36381887ca77b7bab61413ea2ec.
Emitted output uncompressed SHA256: 91da349a53c2b2853513560ef2adbc2324101d4486301f97c111cece7e8bab3a.

900Q unchanged, static paid 317994 unchanged, ops 87067496 -> 87152878. 17 physical seams, 1173 CCX, 204 measured output directions, one private classical bit. All 139264 paired arbitrary dirty-state seam checks passed (C++); full native KickMix 1.0.0 replay succeeded on all 1790 paired shots with identical output/phase/public-register digests and paid counts. The full KMB and physical compiler are local research artifacts delivered separately; CI here compiles the two extracted normalized tensors.

| Panel | Shots | Mean paid before/after | Union failures before/after |
| --- | ---: | ---: | ---: |
| Ordinary | 1024 | 316114.71484375 | 0 / 0 |
| Saved stress | 622 | 316084.04019292607 | 412 / 412 |
| Dense | 144 | 316053.69444444444 | 70 / 70 |

These are different measurement seeds from the published 316094.00 paired baseline; not a new official score. Independent C++ full tape replay also passed with its own measurement RNG. Normalized native KickMix CI: 17408 paired checks, no state or phase mismatch, 101 and 67 paid per chart unchanged. Lean 4.35.0 six declarations, all axiom-free. Strict CI success: https://github.com/corcondor/gvqcc/actions/runs/46162602367.

The measured-adjoint rewrite directly transports phase debt without restoring the measured nonlinear output. It does not implement full adaptive Euclidean degree dispatch, and it does not produce any paid improvement or fix existing stress errors. Do not submit or merge as an improved circuit.

## Exact original 316094.00 paired comparator

Recovered the original input generator, saved panel, 256-shot batch schedule and measurement seeds. Ran native KickMix 1.0.0 locally on both exact complete KMB hashes.

| Panel | Shots | Mean paid before/after | Union before/after |
|---|---:|---:|---:|
| Distribution | 1024 | 316094.000 | 0 / 0 |
| Saved622 | 622 | 316091.48713826365 | 411 / 411 |
| Dense weights | 144 | 316149.6666666667 | 70 / 70 |

All four paired difference counts zero. Same exact 316094 baseline, no paid or score gain. Full native log, verifier, source and receipts delivered in the research archive. No change to main or competition submission.
