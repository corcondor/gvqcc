# Credits for family_32695.zip (chemistry, 3,269.5 loader Toffolis per pass)

Original builder: **Syed Asad Ali** (Apache-2.0). Lineage and the full list of credits are the same as in
`../claude-chem3271-20261127/NOTICE.md`.

- Base: `family_3270_351710.zip` of [PR #179](https://github.com/corcondor/gvqcc/pull/179) (V75, Antigravity side),
  including its 231-Toffoli head loader for bank 5 and the angle table (`submission.npz`).
- Changed here: `angle_k_0.kmb` only, our own build: 241 CCX plus one conditionally executed CCZ
  (mean 241.5; was 242), built with `loader/make0m.py` (smallest-shared-dimension early set, greedy chip order,
  spill and rematerialisation, `loader/build3.py`).
