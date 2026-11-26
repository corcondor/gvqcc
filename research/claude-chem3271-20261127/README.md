# Chemistry 3,271 Toffolis per pass (official PASS) + cheaper invsqrt (official PASS)

**運用ルール（2026-11-27 オーナー指示）: コンペへの提出は、明示の指示があるまで行わない。Kaggle での実験は可。**
このブランチの内容は未提出です（提出の記録は `SUBMISSIONS.md`）。

## Results

| artifact | official verifier (unchanged) | numbers |
|---|---|---|
| `family_3271.zip` — 15 angle loaders + `submission.npz` | dfthcsos PASS, default and a fresh salt, 78,016 shots each | **cost 247,801,621.46**, 3,271 loader Toffolis/pass, T 13,042, 405 qubits, lambda_eff 46.914266, 399,252 instructions |
| `invsqrt_C1.zip` — `invsqrt.kmb` | invsqrt PASS, 200,540,928 shots | **cost 60,865.16** (b806: 60,918.318), 37 qubits, mean Toffoli 1404.625 |

With the DQI circuit used before (4b572141, not included) the local combined score is 33.32778.

## What changed
- **Loaders.** Base: the public goodpjw2008 loaders (3,306/pass) as shortened to 3,275 in
  [PR #179](https://github.com/corcondor/gvqcc/pull/179). Banks 1, 5, 7, 11 replaced by our group-start construction at
  **232** Toffolis (were 233), compressed with the affine-block resynthesis from PR #179
  (`src/compress_new_heads.py` imports that script). Bank 0 is our 242 loader. Table (`submission.npz`) is unchanged
  from PR #179. Exact check on all 1,219 addresses and every measurement outcome, forward and reverse: PASS
  (`verification/xcheck_3271.txt`).
- **invsqrt.** On top of b806, a measured flag's correction is paid by Clifford terms plus one CCZ on live values
  (certificate tools in `src/invsqrt_certificate/`); data and phase identical on all 3,133,452 inputs.

## Notes from the experiments (for other sessions)
- Head loaders with 13 relation columns give 232 on the first seed in about 5 minutes per head on a Kaggle CPU kernel.
  Asking for 14 relations from four-element columns changes nothing (only 13 exist); 231 needs a forced five-element
  column (`fivecol.py`), job in `src/head_search_jobs/job_231.json` (running).
- Our segment re-synthesis (`src/experimental_*.py`) did not beat the PR #179 compressed wired loaders; the lazy affine
  variant halves unoptimised wired loaders but grows already-compressed ones.
- The kickmix verifiers also run locally on Windows with identical results (chemistry about 1-2 minutes).

## Lineage
See `NOTICE.md` (original builder: **Syed Asad Ali**, Apache-2.0; chemistry loaders and weights: goodpjw2008's public
"QCC | Shorter Chemistry Loaders"; table design Team ThemBones and Almond Labs; loader line maoxin123 and others).
