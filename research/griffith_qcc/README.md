# Griffith → GVQCC: trainable exact XAG compiler (experimental)

This is a **GVQCC-specific original adapter**, inspired by [Griffith](https://github.com/tsukushi-gate/Griffith). It is **not a fork of Griffith** and is not affiliated with Griffith authors. The connected GitHub write API does not currently expose a repository-fork endpoint. This branch is intended for discussion and testing before any merge.

Upstream code studied:
- `Griffith/griffith_logic/layers/lut.py` — learnable Boolean function probabilities
- `Griffith/griffith_logic/layers/dwn.py` — learnable connections
- `Griffith/griffith_logic/analysis/sat_capacity.py` — exact realizability checks
- `Griffith/griffith_logic/analysis/dontcare_repair.py` — legal-input don't care handling
- `Griffith/griffith_logic/export/abc_opt.py` — independent equivalence verification
- `Griffith/tools/nas/search.py` — Pareto search with reproducible trials

Our implementations are newly written and released under Apache-2.0. Preserve Griffith's original notices if copying upstream code in a later PR; see `UPSTREAM_LICENSE.md`.

## What works now

1. A bit-exact, multi-output `XAG` IR with arbitrary affine (XOR) inputs to reusable AND products.
2. Full enumerative one-AND synthesis for `n<=6`, **shared across all requested outputs**.
3. Differentiable gate fan-in and XOR readout in PyTorch (`train.py`), with exact hard-circuit acceptance. A trained network that merely fits sampled inputs is rejected.
4. A KickMix KMX **reversible oracle** emitter: `CCX` computes products, `HMR` and measurement-conditioned `CZ` clean work with phase correction. A separate small-domain analyzer checks value, scratch, and every HMR branch.
5. A direct read of real Goodpjw V8 `angle_words` in all 15 banks: five temporal conserved helpers from `bit5 XOR bit6`, low-only rank 10; the all-zero-MSB gauge **violates that contract**. This is a blocker in the existing six-extra-AND cache, not a proof of global optimality.
6. `joint.py` supplies a fail-closed joint physical/hardware cost interface: an unverified circuit or an invalid FeMoCo solution is **never marked score-comparable**.

## What it does NOT yet do

- The code does not fork Griffith's complete repository, and it does not train all V8 `R,B,C,J,b_rot,W,H2_I` variables in a single differentiable graph.
- The local 4-bit witness is **not a replacement for the full 11-bit/15-bank oracle**. Cached products shared across separate ANGLE calls require an explicitly valid persistent layout and KMB verification.
- The code does not modify the existing V8 18-file submission and has **no newly verified leaderboard score**.
- KickMix native simulator is not bundled. The pure-Python restricted KMX proof does not replace official native validation.

## Repro

```bash
# From this directory
PYTHONPATH=src python -m unittest discover -s tests -v
GVQCC_V8_NPZ=/absolute/path/to/public_v8_parent.npz \
GVQCC_GAUGE_NPZ=/absolute/path/to/public_v8_temporal_gauge.npz \
    PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m griffith_qcc.chemistry /absolute/path/to/public_v8_parent.npz
```

`torch` and `numpy` are optional extras for neural training and actual chemistry data respectively.

## Roadmap / joint optimization architecture

The important target is not low ANF count or zero MSBs. Optimize the combined actual score subject to validity:

`min lambda_eff * T_total * Q_total` subject to FeMoCo physical constraints, 128-qubit loader cap, exact forward and reverse word transitions on every valid address and all HMR outcomes, plus two official KickMix salt panels.

For a candidate physical solution, the joint loop should alternate (a) `W/H2_I` and quantized words (`R,B,C,J,b_rot,tree`), (b) **discrete sign gauge with conserved nonlinear helpers kept as a learnable option**, (c) XAG gate/wiring training, (d) exact synthesis and schedule with HMR correction, and (e) native verifier scoring. Keep multiple candidates on a Pareto frontier, not one current local minimum. Only the exact small-cut core and acceptance interface are implemented in this PR.

Use the 15-bank `bit5 XOR bit6` invariant as a warm-start, **not a fixed rule**: alternate architectures may abandon it if their true total KMB cost is lower. Missing this invariant causes the published fixed-cache emitter to fail with `rank 5 != rank 10`; repairing the emitter and considering all helper representations is part of the next optimization stage.

## Measured real-V8 local cuts (reproducible; not the full loaders)

For `public_v8_parent.npz` (1219 addresses), `experiments/train_v8_cut.py` produced:

| Cut | Prior naive ANF nonlinear monomials | Exact XAG AND products | Verification |
|---|---:|---:|---|
| ANGLE bank 4, bit 8, first 16 legal addresses | 5 | **1** | 16 addresses, 2 HMR branches, arbitrary XOR target |
| ANGLE banks 13+14, bits 8+4, high block 3 | 2+2=4 | **1 shared** | 16 addresses, 2 HMR branches, arbitrary two-bit XOR target |

The first was learned **without a hard algebraic seed**, with 4/8 random restarts finding an exact hard witness. The second is constructed by exhaustive shared-factor synthesis; no neural convergence is claimed for that witness. `experiments/local_search_receipt.json` contains full reproducibility metrics and KMX examples. These are **local mathematical subfunctions**. They are not a valid redesign of 15 independent ANGLE KMBs, and no 4T or 3T full-loader improvement is claimed.

The complete V8 table has 0 violations of its five conserved temporal helper functions. The zero-MSB temporal gauge has **42,743 violations** of those same 5×14×1219 equalities and 3,015 low-only violations, despite having equivalent FeMoCo physics. This explains why zero-MSB is insufficient as a low-Toffoli objective. The next optimizer must learn *whether to retain or recompute* these nonlinear cached features, under the 128Q cap.

Reproduce with an externally supplied V8 NPZ; the 1219×75 proprietary/public-frontier table is **not** vendored here:

```bash
PYTHONPATH=src python experiments/train_v8_cut.py --v8 /path/to/public_v8_parent.npz --output local_output --trials 8
```

### Joint candidate grid (physics + learned Boolean cuts)

The experimental `joint_candidate_grid.py` performs a reproducible **co-evaluation** with the full FeMoCo numerical evaluator for each supplied (W, H2_I, 7-bit angle table, Givens tree) NPZ and trains an exact local XAG for that table. It reports the cached-helper contract and keeps the result **unscorable** until the corresponding 15 native KMBs and the full verifier pass. It is not yet a fully differentiable end-to-end physical optimizer.

```bash
# Full external FeMoCo reference NPZ is required; not committed to GitHub.
PYTHONPATH=src python experiments/joint_candidate_grid.py \
    --reference /path/to/chem_gpu_inputs.npz \
    --candidate /path/to/public_v8_parent.npz /path/to/v8_joint_physical_parent.npz \
    --output joint_grid.json --trials 4
```

A joint-training implementation must treat discrete gauge and angle words as structured variables, learn W and H2_I with the exact physical gradient, and use the generated KMB's CCX/HMR/width/salt cost **only after** the hard proof gate. The optimizer cannot safely mark a soft XAG fit or a physics-only lower lambda as a new score.

## New exact result: all temporal tags are trainable 5×LUT4 variables

For every 7-bit angle word `w`, let `t(w) = ((w >> 5) ^ (w >> 6)) & 1`. The four physically equivalent Givens angles induced by incoming, parent-output and child-output sign bits obey the *exact* Boolean identity:

```
    t(w') ^ t(w) = input_sign ^ parent_sign   if w not in {32,96}
                   input_sign ^ child_sign    if w in {32,96}
```

The identity was tested for **128 original words × all 8 sign combinations**. In a fresh-child Givens tree, the selected edge goes to a later node or final leaf. Thus any prescribed tag sequence for one row is realizable by reverse substitution, choosing the final global sign so the root starts with sign +1. The orbital vector is preserved up to a global ± sign, and the full FeMoCo physics is unchanged.

For valid V8 helper codes, prescribe the same five functions `h_j(a_low)` in each of the 15 batches. There are **five 16-entry Boolean LUTs = 80 trainable bits**. Restricting their span with constant and four low address bits to rank 10 preserves the existing low-cache *premise* (six additional ANDs to complete the 16-dimensional 4-bit Boolean algebra). This is a far smaller, physically invariant search space than unconstrained 1219×75 angle edits. It does **not** make every XAG/KMB plan reusable: the nonlinearity tensors and phase/scratch schedule must be recompiled and proven.

Applied to the physical-PASS V8 candidate (`lambda_eff=46.913759041834915`) that previously broke ten temporal helper equalities, `temporal_gauge.project_table()` changed **32 words across seven rows**. All 75×1219 prescribed tags were recovered, the five helper functions regained exact time invariance and rank 10, and the independent FeMoCo evaluator returned the **same** `error_1`, `error_2`, `Lambda`, `E_gap`, and `lambda_eff` to roundoff. An arbitrary direct reversion of the ten modified words instead caused `error_1 > 20 mHa` and failed.

A first online bandit-style search of these 80 LUT bits was executed for 300 proposals. The fifteen-bank low×high interaction **rank proxy stayed 7373 → 7373**. This is a negative *proxy* result, not a full Toffoli optimum; the next critical engine is to backpropagate **actual KMB compilation cost**, measurement-phase corrections and 128Q peak into these LUT-code variables, and jointly update W/H2_I and tree/angle words. `helper_code_search.py` implements a full 15-bank fast screening proxy, not a surrogate that may be reported as actual gate savings.
