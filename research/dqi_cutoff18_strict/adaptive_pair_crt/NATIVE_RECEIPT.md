# Native KickMix validation, 2026-11-28

Existing draft PR #235; source generators `crt882.py` and `legacy_crt.py` in this directory. Reuses the exact GF12 42-CCX multiplication from #190 and the archived adaptive CRT tape from #235. The original 17-node chart is G^2, not the extended G^2*g18 chart. The legacy regression uses 20 saved original all-pole failures plus 4 additional saved all-pole failures from #233; fixture data is used only in regression tests, not the codec.

Actual native Vercel sandbox run, Python 3.14.4, kickmix==1.0.0. Strict Lean CI for the 16 existing theorems: https://github.com/corcondor/gvqcc/actions/runs/46068694980 (success at 7ec0237f0f5055caa6572b9920e65c6a7128e142). This does not prove the new legacy tape end to end.

| Tape | Q | Operations | CCX | CX | Native checks |
|---|---:|---:|---:|---:|---|
| Extended CRT forward | 882 | 260239 | 9288 | 250951 | 346/346 |
| Original 17-node CRT forward | 882 | 233924 | 9078 | 224846 | 352/352 |
| Original 17-node CRT reverse | 882 | 233924 | 9078 | 224846 | 352/352 |

No value, dirty ancilla, or phase errors in these native codec tests. Legacy corpus: 24 saved all-pole, 128 synthetic all-pole, 72 ordinary all-weight, 128 arbitrary. All 24 saved cases recover the locator and reconstruct all 70 moments using the derived error amplitudes.

SHA256:
- archived extended raw tape: e0c8844a3b260d7215f40457137fa978af821e71d0098ab4ccdafa1f9be3d927
- extended KMB: 2ea9890dab6f1faac374df4d411cf279082ae23e08a2b84f72561e8af10c5bbb
- legacy raw tape: 649f4183dd7c5b0560ad7ac55285e884e481ced1b1428caee18dd2ac8542cd69
- legacy forward KMB: fdaa1128c1dbe413649abf5e67383b2bec0e20a9df7014cc07308564a6272e88
- legacy reverse KMB: 11277bc60e412b818426bcf890164be644d7b72a06baf011cf5f59e9032f4108
- exact original fixtures, little-endian u16: a1d52d29338d0699f56f004f49d1a827903af9d62ccb2dcfa05787a2d4a086cf
- crt882.py: 834a7c72b9fb3e61e2d6d2c27c52930207c6c58e6e9322fa7a8c73a23d33dc38
- legacy_crt.py: b00b47cf5c4af80919a19e925041890a49fefeee281e32148288c10cf25f6136

Reproduction: install kickmix==1.0.0 and numpy, run python crt882.py then python legacy_crt.py. Both scripts emit native KMB files. The full #233 donor and #234 phase-oracle archive were recovered from the library, but not transferred into this native sandbox. Do not interpret codec PASS as full-donor repair or zero phase-oracle errors. Original phase scan/guard integration remains unverified. No submission or main merge.
