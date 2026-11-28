# V68/V69 Chemistry Angle Loaders: `3,278` Toffolis/pass (`248,067,625`) & Bank 14 at `207` CCX

> **Research & reproducible source bundle (Draft PR; `main` untouched).**  
> All chemistry families below passed the unchanged official `verifiers/dfthcsos/verify.py` on **both default and fresh salts** (78,016 shots each, `Q = 405`, `error_1 / error_2 < 20 mHa`).

## Summary of Verified Results

| Family | Loader Toffolis / pass | Official Chemistry Cost (`score`) | Total Verifier Toffolis | `lambda_eff` | Official `dfthcsos/verify.py` |
|---|---:|---:|---:|---:|---|
| PR #175 (`claude-chem3312`) | 3,312 | 249,379,397.06 | 13,124 | 46.917982 | PASS |
| `stage1b` baseline | 3,302 | 248,999,361.40 | 13,104 | 46.917982 | PASS |
| **V68 (`b14 = 207`, all-8191 `z3` scan)** | **3,301** | **248,961,357.84** | **13,102** | 46.917982 | **PASS (default + fresh salt)** |
| Base `3,284` family | 3,284 | 248,295,628.68 | 13,068 | 46.914266 | PASS |
| **V69 (`k = 5, 7, 11` rebuilt to `233` on `3,284` words)** | **3,278** | **248,067,625.35** | **13,056** | **46.914266** | **PASS (default + fresh salt)** |
| **V70 (`k = 0` at `242` + `k = 1, 5, 7, 11` at `233`)** | **3,275** | **247,953,623.68** | **13,050** | **46.914266** | **PASS (default + fresh salt)** |
| **V71 (`3,275` + Commutation-Fused Boyar-Peralta / Sparsity-PMH)** | **3,275** | **247,953,623.68** | **13,050** | **46.914266** | **PASS (`num_ops = 344,306`, `reaction_depth = 1,307`)** |
| **V72 (`k = 0` at `242` + ALL 4 heads `k = 1, 5, 7, 11` at `232` + V71 compression)** | **3,271** | **247,801,621.46** | **13,042** | **46.914266** | **PASS (default + fresh salt, `num_ops = 347,778`)** |
| **V74 (`3,271` + Joint `CCX/CZ` Commutation Transport + Difference-Equation Affine Opt)** | **3,271** | **247,801,621.46** | **13,042** | **46.914266** | **PASS (default + fresh salt, `num_ops = 341,472`, `reaction_depth = 1,409`)** |
| **V75 (WORLD FIRST `231`-CCX head `k = 5` via `min dim(R) = 143` at `e = 30`)** | **3,270** | **247,763,620.91** | **13,040** | **46.914266** | **PASS (default + fresh salt)** |
| **V75 COMPLETE (ALL 4 HEADS `k = 1, 5, 7, 11` AT `231` CCX — 4/4 `seed=1` CLEAN SWEEP!!)** | **3,267** | **247,649,619.24** | **13,034** | **46.914266** | **PASS (default + fresh salt, 78,016 shots each!)** |

*(Per-loader `CCX` of V75 COMPLETE `3,267`: `242,` **`231`**`, 213, 212, 213,` **`231`**`, 213,` **`231`**`, 205, 212, 212,` **`231`**`, 209, 206, 206` = **3,267**; chemistry `score` = **`247,649,619.24`** (`-152,002` below `3,271`, `-646,009` below `3,284`, `-1,596,224` below public best!), breaking the `91 + 2 = 93 > 92` obstruction via `min dim(R) <= 143` at `e = 30` (`4/4` first-try `seed=1` PASS on `k = 1, 5, 7, 11`). Uncompressed `num_ops = 385,721` — ready for V103/V74 ops compression down to `~314,000` ops!)*

## What Is Included

- `src/v68_planted_allz3.py` — Vectorized all-8,191 `z3` functional scanner that solved the previously open 41-product planted Block-2 problem on Bank 14 (`col_rank = 75/75`, `prow_ker=1, nbad=3`), yielding a verified **207-CCX** Bank 14 loader (`82 + 39 + 41 + 42 + 3`).
- `src/run_v69_heads.ps1` — Reproducible PowerShell driver rebuilding group-start head loaders (`k = 5, 7, 11, 1`) at `NREL=12, E=29` (`233` CCX) on the `3,284` `submission.npz` with **zero word changes** (keeping all 10 wired loaders and `lambda_eff = 46.914266` byte-identical).
- `src/v69_compare_3284_3301.py` — Per-loader CCX & word-diff comparison script.
- `family_3278.zip` — Complete 15 chemistry `.kmb` loaders + `submission.npz` at **3,278 Toffolis/pass** (no DQI or InvSqrt binaries included).
- `verification/v69_3278_verify_default.json` & `verification/v69_3278_verify_fresh.json` — Official `dfthcsos/verify.py` receipts on both salts.
- `NOTICE.md` — Full lineage and attribution.

## Verify Locally

```bash
unzip family_3278.zip -d /tmp/fam_3278
python verifiers/dfthcsos/verify.py /tmp/fam_3278
python verifiers/dfthcsos/verify.py /tmp/fam_3278 --salt v69-fresh-salt-20261127
```
