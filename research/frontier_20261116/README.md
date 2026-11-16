# 2026-11-16: C43/C42 + public 28.09 frontier reproduction

Goal: attempt a genuine **C=43 or 42** FeMoCo factorization under the unchanged 8-bit public ANGLE table, while reusing publicly available Apache-2.0 circuit improvements and the separately verified **corcondor DQI562** KMB.

## Files

* `rank43_42_joint_gpu.py`: Float64 PyTorch GPU/CPU fit of native `(W,d)` with `d=H2_I-sum_b W`, physical-projector Gram initializers, optional prior C43/C42 warm starts, and exact final calls to `evaluate_dfthc_angle_words`. Only C43 and C42 are enabled. With `--angle-dir`, a numerically eligible candidate is reverified by the complete official 78,080-shot verifier. No automatic Kaggle submission.
* `frontier_hybrid_builder.py`: Source-level and SHA256-level reuse of maoxin123's public v27 44-qubit invsqrt, its pinned 15 ANGLE KMBs/NPZ, and our unchanged official-PASS DQI562. The notebook's source is **parsed as data**, not executed. It produces an 18-member candidate ZIP and a hash manifest. It does **not** qualify the assembled ZIP as officially verified.
* `frontier_score_gate.py`: Quantifies C rank cost and DQI Q/Toffoli cost exchange; never infers feasibility from a hypothetical rank reduction.
* `test_frontier.py`: Deterministic tests for numeric bounds, Gram projection and source parsing.

## Official acceptance and reproducibility

The chemical reference cost is `lambda_eff * T * Q`. Decreasing C decreases the **state preparation model**, not the number of calls or Toffolis in the ANGLE KMBs. The current pinned 4025-CCX-pass family is T=14712 at C44, T=14634 at C43, T=14555 at C42, Q=427 in this model; actual full verifier resources must agree.

Prior own FeMoCo research found C43 `error_2=0.021132979193` and C42 `error_2=0.023037624547`, both outside the strict 0.020 gate. The model starts from an official *existing* C44 fit; neither rank is claimed feasible or globally impossible. Existing independent high-rank R1/B2926/C307 PASS with `error_2=.01474361` is **27.4x more expensive** and is not a valid cost-saving replacement.

Public 28.09 component costs: invsqrt 75006.38, DQI 347375470571.73, chemistry 294762732.98. Their rounded local composite score is 28.09487172. Our prior official local DQI562 cost is 347373921975.41; swapping only that task into the *public* 28.09 set gives a conditional arithmetic score `28.09491347`. **No new 18-member composite has passed all three official verifiers in this branch; no public leaderboard score or submission is claimed.**

Rank 43 and 42 at identical lambda are only conditional scores around 28.14474 and 28.19557. With other components held fixed, the lambdas needed to reach 28.3 are approximately 46.1536 and 46.4041, respectively. That is substantially lower than current ~46.92. These targets are not proof of achievable chemistry quality.

DQI is costed by `R(epsilon_plus) * Q^2 * T`. At unchanged R, reducing Q from 890 to 880 allows about **8,414 additional Toffolis** without increasing DQI cost. If the error rate / repetition factor changes, recompute with the ratio; do not treat the allowance as unconditional.

## Execution on Kaggle CPU/GPU

Requires Python 3, NumPy, SciPy, PyTorch, unchanged official `dfthcsos` verifiers/FeMoCo reference and an importable `inverse_v2_chemistry_refit.FixedAngles` from this repository. On Kaggle, attach the official competition data and an input directory holding the public **15 ANGLE KMBs and the pinned C44 factorization**. These files are not present in GitHub because the benchmark reference and large KMBs are distributed separately.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python research/frontier_20261116/rank43_42_joint_gpu.py \
  --base-npz /kaggle/input/your-public-family/dfthcsos/submission.npz \
  --angle-dir /kaggle/input/your-public-family/dfthcsos \
  --output-dir /kaggle/working/c43_c42_v1 \
  --ranks 43 42 --device cuda --steps 1200 --seeds 3 \
  --loader-t 4025 --assert-t44 14712 --assert-q44 427
```

For a CPU smoke test explicitly set `--device cpu --steps 2 --seeds 1`. An optional `--warmstart-dir` with `C43_seed0.npz`/`C42_seed0.npz` lets past ALS/GN checkpoints be reused.

To construct a source-pinned hybrid for **separate full official verification**:

```bash
python research/frontier_20261116/frontier_hybrid_builder.py \
  --public-notebook-raw /path/to/pull-api-response.json \
  --public-chemistry-dir /path/to/public/pinned/18-contents \
  --own-verified-zip /path/to/submission_graph562.zip \
  --output /kaggle/working/hybrid_candidate.zip
```

The notebook pull JSON can be fetched from `https://www.kaggle.com/api/v1/kernels/pull/maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier`. Omit `--public-notebook-raw` to fetch it read-only online when network is enabled. A standard `kaggle kernels pull` output `.ipynb` is **not** the outer API response expected by this parser. The public chemistry files can be obtained from the notebook's attached dataset `maoxin123/qcc-frontier-dqi-chem-mirror` or the matching public output files and must match the SHA256 entries in the notebook exactly. We do not run a source notebook or use unverified DQI inputs.

Do not submit a candidate merely because the source files hash-match or because numeric `error_2 < 0.020`: also check `error_1`, gap, lambda, circuit consistency, Q/T, official full shot counts, and full 18-member component provenance.

## Source credits

* maoxin123's public v27 44Q invsqrt notebook, Apache-2.0: https://www.kaggle.com/code/maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier
* masumhuq public composite notebook, Apache-2.0: https://www.kaggle.com/code/masumhuq/qai-per-task-max-composite-28-09
* manwithacat public circuits dataset with original circuit credits and licences: https://www.kaggle.com/datasets/manwithacat/vqcc-apache-public-circuits
* Official rules and cost formula: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
* Local DQI562 verification, member SHA and exact score: prior user-owned `submission_graph562_scorecard.json`; not copied into this repository branch.
