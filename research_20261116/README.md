# 2026-11-16 public frontier / verified local 562 hybrid

## Evidence and result

- Public maoxin123 28.09 source (Kaggle API Python notebook), official per-task costs:
  invsqrt 75,006.38 (Q=44), DQI 347,375,470,571.73 (Q=890),
  chemistry 294,762,732.98 (R/B/C=8/143/44, Q=427).
- Our earlier `submission_graph562.zip` local official 102,400-shot DQI proof:
  **347,373,921,975.41064** (Q=890; mean T=368,137.8485742187; 0 value/phase errors).
  That is 1,548,596.31936 cheaper than the listed public DQI.
- Componentwise combined cost **would** yield GM **28.094913467688727**.
  **No combined ZIP has been built or full-verified here; no Kaggle submission.**
- Reference costs follow Kaggle official metric. Do not compare raw CCX count
  alone. In particular DQI cost is `R(epsilon_+) * Q**2 * T`;
  if Q falls and R stays fixed, increased T can be economically beneficial.
- Historical C43/C42 ALS+GN attempts failed at e2=0.02113298/0.02303762.
  C43/C42/C41 relaxed theoretical error bounds under 0.02 do **not** establish
  a constructible, acceptable 8-bit circuit.
- Independent R1/B2926/C307 precision control reached e2=0.01474360945633713
  in 192,128 official chemistry shots, but cost was **8.076 billion**, so it
  is not a cost improvement over the accepted C44 294.763 million line.

## Files

- `frontier_cost_gate.py`: actual three-task cost arithmetic, conditional
  C43/C42/C41 break-even thresholds for GM28.3, and DQI Q/T trade-off.
- `chemistry_cascade_gpu.py`: experimentally initializes C43/C42/C41 with
  physical Gram-weighted rank projection, runs cost-aware differentiable
  constrained numerical search on PyTorch CUDA (CPU fallback), and rechecks
  each completed candidate with the official fixed-8bit numerical evaluator.
  These scripts do **not** reuse a float-only surrogate for the final numbers.
- `../test_frontier_cost_gate.py`: arithmetic and safety regression tests.

## Run

At repository root:

```bash
python research_20261116/frontier_cost_gate.py --target 28.3 \
  --out /tmp/verified-frontier-28-09-costs.json
python -m unittest test_frontier_cost_gate -v
```

The optional GPU search depends on `inverse_v2_chemistry_refit.py`, the complete
official `dfthcsos` verifier package, and verified FeMoCo FCIDUMP/fixed_shifts
on the research machine. Input must be the actual C44 `submission.npz` with
unmodified, 8-bit `angle_words` matching the 15 verified angle-loader KMBs.
Pin the baseline and source SHA-256 before promoting a candidate.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  research_20261116/chemistry_cascade_gpu.py \
  --base-npz /kaggle/input/your-verified-c44/submission.npz \
  --out-dir /kaggle/working/c41_43_search \
  --device cuda --steps 1500 --seeds 3 --ranks 43 42 41
```

The script refuses a missing GPU when `--device cuda` is explicitly requested
and refuses non-R8/B143/C44 geometry or inconsistent baseline T/Q. Each NPZ
is marked `NUMERIC_ONLY_REJECTED` or `ELIGIBLE_FOR_NATIVE_CHECK`.

**Even ELIGIBLE is not a circuit PASS.** Before packaging/submit, preserve
the 15 exact loader KMBs, run the unchanged 78,080-shot official chemistry
verifier (both errors <=0.020, strict Lambda/gap floors), and full DQI/invsqrt
checks. Calculate all three costs from receipts on the candidate bytes,
and only promote if GM is higher than the currently selected verified submission.
No hash/seed selection or weakened validation. Do not describe the historical
C43/C42 failures or projected hypothetical 28.3 scores as official wins.

## Source and attribution

- Kaggle public 28.09: https://www.kaggle.com/code/maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier (Apache-2.0); and https://www.kaggle.com/code/masumhuq/qai-per-task-max-composite-28-09
- Historical user-owned evidence: `submission_graph562_scorecard.json` and
  `ANTIGRAVITY_STRUCTURAL_FUSION_RESULT_JA.md` retained outside this repository
- Additional upstream contributions credited by the Kaggle notebooks:
  Syed Asad Ali, Hayato Hikawa, boristown, Lera/marculera, Jeff Emerson, Leo Tang.
  Reuse their original license and notices with copied compiled KMB/NPZ artifacts.
- Official competition cost definition:
  https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation

## This turn's measured execution boundary

Cost gate: **7 local unit tests PASS**, reconstructed public GM verified
against author figure, and C41/42/43 conditional table generated.
GPU search: numerical kernel compiled and small synthetic contraction,
autodiff and rank initialization tested on **CPU only**. No real FeMoCo
optimizer run, no new KMB compilation, no competition submission.
