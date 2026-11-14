# C44 fixed-word score optimization: no accepted improvement

## Outcome

**No new C44 factorization obtained in this experiment both satisfies the official numerical gates and improves the chemistry score.** The existing submission and all 15 loader circuits remain unchanged. Lower intermediate values of `lambda_eff` are not reported as score improvements.

The experiment optimized `W` and `H2_I` jointly at `R=8, B=143, C=44, N=76, brot=8, J=5`. Every recorded endpoint preserves the Givens tree and all **91,500 eight-bit angle words** exactly: the table shape is `1220 × 75`, representing **732,000 logical angle bits**. This equality was independently rechecked from each saved NPZ during result collection.

With the same words and circuits, the resource counts remain **4033 loader CCX per pass, 14,728 total Toffoli, and 427 total qubits**. Therefore only `lambda_eff` can change the cost in this experiment. The reproduced baseline is `46.906589508623554`; the user reported a separate baseline of `46.905894137`, whose exact weight arrays were not available here. Neither baseline was improved by an admissible new endpoint.

This is a finite local numerical search, not a lower bound or proof that fixed-word C44 improvement is impossible. The root agent's C43 optimization and global spectral bounds are separate experiments in `score_chemistry_c43_whiten_converged.json` and `score_chemistry_rank_bound.json`.

## Numerical contract and measured endpoints

All final metrics below come from the **unchanged** `evaluate_dfthc_angle_words` numerical evaluator with the exact reference FCIDUMP and fixed shifts. The acceptance gates are all required:

- `error_1 <= 0.020 Ha` and `error_2 <= 0.020 Ha`;
- raw `Lambda > 49.0`;
- `E_gap > 3.914898 Ha`, with strict inequality;
- a finite `lambda_eff` and `0 < E_gap < 2 Lambda`.

The score formula is `lambda_eff × T_total × Q_total`. A formula evaluated at a rejected point is only a **comparison cost**, not an official circuit score.

| Endpoint | Exact lambda_eff | error_1, mHa | error_2, mHa | E_gap, Ha | Result |
|---|---:|---:|---:|---:|---|
| Reproduced baseline | 46.906589509 | 19.999998000 | 19.999998499 | 3.914898002 | Previously verified baseline |
| Joint C44 descent, before restoration | 46.901644074 | 19.995388138 | 20.033824182 | 3.914898917 | Reject: error_2 |
| Error-only restoration | 47.279518054 | 19.999980000 | 19.999980000 | 3.978374078 | Numerical gates satisfied; cost is worse |
| H2_I-only polish of restored W | 47.222923421 | 19.999980175 | 19.999980000 | 3.968068624 | Numerical gates satisfied; cost is worse |
| Fresh conditioned descent | 46.905292409 | 19.999997946 | 20.004006507 | 3.914898089 | Reject: error_2 |
| Trace-smoothed continuation | 46.905526007 | 19.999989135 | 20.003236309 | 3.914905575 | Reject: error_2 |
| Final solve with explicit score budget | 46.905827475 | 19.999860527 | 20.003194680 | 3.914955938 | Reject: error_2 |

The final attempt constrained the search to `lambda_eff <= 46.90585`, which would beat the user's reported baseline if all accuracy gates passed. Its exact `error_2` still exceeds the limit by **3.1946799606 µHa**. It is not a usable submission.

No new full circuit verification was run for these rejected or more expensive candidates. The pre-existing loader proof remains applicable because their words are unchanged, but that does not turn an inaccurate factorization into a valid chemistry submission. The root's `score_dfthcsos_fixed_words_verify.py` is the final full-verification gate for a future numerically admissible improvement.

## What was implemented

### 1. A stable search objective outside the accepted domain

The earlier evaluator clamps an invalid square-root argument to a tiny positive value. A trial step crossing `E_gap=0` can consequently produce enormous gradients and false zero-step convergence. The new driver searches with

\[
F=\frac{g(2\Lambda-g)}{2\lambda_{\mathrm{ref}}}.
\]

On the accepted positive domain this preserves the ordering of `lambda_eff`. Outside that domain it provides a finite differentiable extension for line search. Acceptance still uses the original unsquared exact quantity and all original gates.

### 2. A faster algebraic contraction

Let `O_rb = u_rb u_rb^T` and `d_rc = H2_I_rc − Σ_b W_rbc`. Instead of reconstructing all 352 full `X_rc` matrices on every evaluation, compute

\[
c_{rb}=\sum_c W_{rbc}d_{rc},\qquad
h'=h_{\mathrm{base}}-\sum_{rb}c_{rb}O_{rb}.
\]

For any matrix derivative `A`, its projection onto `X_rc` is also obtained without materializing `X_rc`:

\[
\langle A,X_{rc}\rangle
=\sum_b W_{rbc}\langle A,O_{rb}\rangle.
\]

`score_chemistry_fast_model.py` implements this contraction. Three comparisons against the original analytic evaluator gave metric/constraint differences at most `1.14e-11` and scaled derivative differences at most `5.15e-8`. The observed evaluation time changed from approximately **0.132–0.151 s to 0.032–0.034 s**, about **4.1–4.5×** faster in the final check. This is a classical optimization-runtime improvement; it does not change the quantum score by itself.

### 3. Natural identity coordinates and feature whitening

The driver can optimize `(W,d)` instead of `(W,H2_I)`. The exact chain rule is

\[
\nabla_W^{(W,d)}F
=\nabla_W^{(W,H2_I)}F
+\nabla_{H2_I}F,
\]

where the second term is broadcast over `b`; the derivative with respect to `d` is the former `H2_I` derivative. This removes a repeated sum coupling from the parameterization.

It can also use `Y_r = L_r^T W_r`, where `G_rr = V_r V_r^T = L_r L_r^T`. Then

\[
W_r=L_r^{-T}Y_r,\qquad
\nabla_{Y_r}F=L_r^{-1}\nabla_{W_r}F.
\]

Both transformations are invertible coordinate changes. They preserve the represented factorization; each new coordinate mode is checked by directional finite differences before optimization.

### 4. Conservative smoothing of the one-body trace norm

Smoothing only `|W|` and `|H2_I|` left another nonsmooth term: `Σ_j |e_j(h')|`. At one endpoint, the exact absolute-value kink caused lambda/gap directional derivatives to disagree by about 14%, while the accuracy derivatives agreed and the Hungarian matching did not change.

The optional trace smoothing uses

\[
s_\delta(e)=\sqrt{e^2+\delta^2},\qquad \delta\ge0.
\]

For every real `e`,

\[
0\le s_\delta(e)-|e|\le\delta.
\]

Thus the smoothed gap overestimates the exact gap by at most `Nδ`. The driver requires the **smoothed gap to exceed its internal target by an additional `Nδ`**. This reserve makes the lower-gap condition conservative. At `δ=1e-7` the reserve is `7.6e-6 Ha`; at `δ=1e-9` it is `7.6e-8 Ha`.

The constructor, evaluator, and driver reject negative, NaN, or infinite smoothing widths. Separate positive-epsilon validation confirms the bound for `δ=1e-7` and `1e-9`, checks derivatives, and confirms that setting `smooth=0` restores exact absolute-value evaluation regardless of the configured trace smoothing. Saved checkpoints are checked with all smoothing set to zero, followed by the unchanged official numerical evaluator.

### 5. Explicit treatment of a matching discontinuity

The other observed obstruction is the verifier's Hungarian assignment between decoded one-body vectors and eigenvectors. At the final source point, exactly two assignments changed under both signs of arbitrarily small probes. At a step of `1e-9`, the two observed `error_1` values were

\[
0.019999989143099053
\quad\text{and}\quad
0.020002303046162530\ \mathrm{Ha}.
\]

The approximately **2.314 µHa jump** does not disappear as the probe shrinks. A single smooth derivative therefore cannot describe that crossing.

The optional `--branch-release` does not change or freeze the assignment rule. It tests a bounded deterministic displacement using the actual evaluator, permits a move only when the measured positive-constraint violation merit decreases and `error_1` stays within its allowed bound, then reruns the directional derivative gate. The recorded `1e-6` parameter displacement reduced the merit from `1.0605381504552618e-7` to `1.0604810131678170e-7`; the new local derivative check passed with scaled error `4.06e-5`. Subsequent line searches still failed to reach a feasible lower-cost point. This is a record of a scoped search step, not a guarantee of convergence through every matching boundary.

## Authoritative records

- `score_chemistry_summary.json`: outcome, unchanged geometry, exact word equality, versions, and the final endpoint.
- `score_chemistry_c44_endpoint_records.json`: all 13 saved endpoint records, exact numerical gates, hashes, and comparison-cost labels.
- `score_chemistry_c44_whiten_descent_record.json`: the fresh conditioned descent, including its gradient gate and learned multipliers.
- `score_chemistry_c44_trace_smooth_record.json`: the conservative trace-smoothing continuation.
- `score_chemistry_c44_goal_branch_record.json`: the matching discontinuity, measured branch release, derivative recheck, and final failed endpoint.
- `score_chemistry_fast_model_validation.json`: comparison with the original analytic evaluator at zero trace smoothing.
- `score_chemistry_trace_smoothing_validation.json`: positive-epsilon derivative/bias checks, exact-mode checks, and six invalid-parameter guard checks.
- `score_chemistry_manifest.json`: hashes for the C44 code and evidence bundle.

Rejected NPZ files were not copied into the repository. Their original scratch paths and SHA-256 values are recorded for provenance. The baseline NPZ has SHA-256 `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`.

## Reproduction

The measured environment was Python `3.12.14`, NumPy `2.3.5`, SciPy `1.17.0`, with `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1`. Numerical searches require the existing `inverse_v2_chemistry_refit.py` and `inverse_v2_chemistry_screen.py`, the unchanged verifier modules under the repository's parent `official_sources/Inzainos/verifiers`, and the pinned reference FCIDUMP/fixed shifts. The baseline is read from the parent directory's `dqi_inputs/chemistry_4033/submission_asterios_full.npz`.

From the repository, the principal trajectory can be reproduced with fresh output directories:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score_chemistry_polish.py \
  --out /tmp/gvqcc_c44_descent --seconds 210 --iterations 450 \
  --smooth 0.000001 --penalties 50,250,1250 \
  --offset-coordinates --whiten-weights --fast-model \
  --initial-lag 0.02,2.0,0.0595

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score_chemistry_polish.py \
  --source /tmp/gvqcc_c44_descent/latest.npz \
  --out /tmp/gvqcc_c44_trace --seconds 180 --iterations 600 \
  --smooth 0.000001 --eigen-smooth 0.0000001 \
  --penalties 6250,31250,156250 \
  --offset-coordinates --whiten-weights --fast-model \
  --initial-lag 0.0022432958,2.6375726610,0.0446939335

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score_chemistry_polish.py \
  --source /tmp/gvqcc_c44_trace/latest.npz \
  --out /tmp/gvqcc_c44_goal --seconds 180 --iterations 1400 \
  --smooth 0.0000001 --eigen-smooth 0.000000001 --penalties 1,10,100 \
  --offset-coordinates --whiten-weights --fast-model \
  --initial-lag 0,0,0,0 --objective-weight 0 \
  --lambda-budget 46.90585 --branch-release
```

The two evaluator checks are independently reproducible:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score_chemistry_fast_model_check.py \
  --out /tmp/gvqcc_fast_model_check.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score_chemistry_trace_smoothing_check.py \
  --out /tmp/gvqcc_trace_smoothing_check.json
```

Wall-clock budgets and eigensystem rounding can change a local optimizer's path. The saved records establish the reported outcomes; they do not promise byte-identical new endpoints on a different numerical environment.

## External candidate boundary

The latest external progress supplied by the user is below. These are reported optimizer outputs; their NPZ arrays have not been provided and the numbers have not been independently reevaluated here.

| External task | Reported status | Reported lambda_eff | Reported error_1, mHa | Reported error_2, mHa |
|---|---|---:|---:|---:|
| 1031, `polish_dfthcsos_brot8.py` | Finished | 46.708 | Not supplied in the update | 20.029 |
| 1046, alternating theta/W optimization | Output with `changed_words=0` | 44.16992 | 19.997 | 20.105 |
| 1051, `test_alt_rounded.py` | Polishing with exactly fixed `words0`, as reported; final NPZ pending | Pending | Pending | Pending |

The posted outputs for tasks 1031 and 1046 exceed the 20 mHa threshold in their reported `error_2`. They therefore do not establish an accepted improvement. Task 1051 is the current pending candidate; the earlier intermediate `45.308766 / 20.396 mHa` is superseded by the progress above.

**`changed_words=0` does not transfer a continuous-theta evaluation to the official rounded-word evaluation.** Continuous angles can move within their rounding cells while their integer words remain unchanged. If an optimizer evaluated the vectors, errors, or `lambda_eff` at those continuous angles, its values need not equal the values obtained from the fixed decoded angles `theta = pi * word / 128`. The zero-change log also needs to be checked against all 91,500 actual words and the exact tree in the supplied file. Once that equality is established, the existing loaders can be reused, but the new `W` and `H2_I` must still pass the numerical gates using the integer-word vectors.

**The local failures in this report do not imply that fixed-word improvement is impossible or that the angle table must change.** Further optimization of `W` and `H2_I` may improve the score with the same words if the exact official constraints are met. This experiment provides no impossibility claim about task 1051 or other fixed-word approaches.

The next concrete input is task 1051's exact final `W`/`H2_I` NPZ. It can be merged only with the verified original words/tree and evaluated by the unchanged official numerical evaluator, including the raw `Lambda`, strict `E_gap`, and both error gates. A numerically admissible improvement can then proceed through the root's full verifier wrapper. No new external candidate is treated as verified while those arrays remain unavailable.
