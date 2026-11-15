# Integer-word and weight-transport optimization

## Outcome and attribution

A small chemistry cost reduction has been verified with the unchanged official verifier: **294,988,786.87084424 → 294,988,052.12610483**, a reduction of **734.7447394 (0.000249075%)** against the SHA-bound baseline available in this workspace. The complete 78,080-shot check passed. The accepted candidate changes 20 actual angle words and `H2_I`, preserving the tree and `W`. Its `lambda_eff` is **46.906472675810164**. The final family, including root's separate Clifford reduction, has 408,788 circuit operations while preserving 4033 loader CCX per pass, 14,728 total Toffoli and 427 total qubits. The authoritative full receipt is [score2_chemistry_best_full_verification.json](score2_chemistry_best_full_verification.json).

An earlier candidate changed a free 16-address angle block and then refit `H2_I`. A control restored all 16 words and retained exactly the same `W/H2_I`. It passed with identical lambda `46.9064788348674` and a better first error. **That earlier gain must therefore be attributed to the identity-weight refit, not to a necessary angle change.** Both versions passed full circuit verification. The original-word candidate remains a fully verified fallback, with cost `294988090.85952884` and 408,394 circuit operations; its authoritative receipt is [score2_combined_full_verification.json](score2_combined_full_verification.json).

The accepted second candidate changes 20 actual words with a zero-Toffoli feature patch and refits `H2_I`. Its independent numerical evaluation and complete official circuit verification agree. It improves the original-word fallback cost by another **38.73342401**. The final family SHA-256 is `142af563255af76b2d2097fb5e8cbc61340c583ea70dadeddf7858de501faf84`.

Neither result beats the user's separately reported `46.905894137` baseline, whose exact arrays were not available here. These are measured local improvements against the reproduced baseline, not a reported Kaggle public score. The earlier `score_chemistry_report.md` remains a historical record of an unsuccessful, different local search; the present success does not alter those recorded endpoints.

## Exact numerical endpoints

All values in this table are from the unchanged `evaluate_dfthc_angle_words` with actual integer `angle_words`, the supplied Givens tree, and the pinned FCIDUMP and shifts. Errors are displayed in mHa; the acceptance limit is 20 mHa for each error.

| Endpoint | Changed words | lambda_eff | error_1, mHa | error_2, mHa | E_gap, Ha |
|---|---:|---:|---:|---:|---:|
| Reproduced baseline | 0 | 46.90658950862355 | 19.9999980000 | 19.9999984994 | 3.91489800150157 |
| Verified identity refit, original words | 0 | 46.90647883486740 | 19.9983603705 | 19.9999984994 | 3.91489802000069 |
| Paired-high candidate after refit | 20 | 46.90647267581016 | 19.9999800001 | 19.9999936270 | 3.91489802000069 |
| Paired candidate with all words restored | 0 | 46.90657102491520 | 19.9965144251 | 19.9999984994 | 3.91491432323528 |

The paired candidate changes `angle_words[address, 19] ^= 1` at addresses **0–15 and 1216–1219**, using zero-based indices. These are 16 one-body rows and four two-body rows. `W` remains the original baseline `W`. Its raw `Lambda` is `282.96313136058893` and its factorization SHA-256 is `5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`.

Restoring all 20 words while preserving that candidate's `W/H2_I` still passes the numerical gates, but gives the worse lambda `46.906571024915195`. It is also worse than the retained original-word candidate. Thus the word change lowers lambda by **0.000098349105031 at those fixed weights**, but is not required merely for feasibility. It does not establish that no different optimization of the original words could match or improve this endpoint.

The distinction between the two controls matters. Changing only the first 76 one-body angle rows can affect `error_1`, but not the represented two-body matrices, raw Lambda or gap at fixed weights. Changing the other rows changes the projectors entering `h'`, so both Lambda and gap can change. We evaluated the second control explicitly rather than transferring the first control's invariance claim.

The remaining gates are raw `Lambda > 49`, strict `E_gap > 3.914898`, finite lambda, and `0 < E_gap < 2 Lambda`. The paired candidate's complete official verification observes cost `294988052.12610483` with the stated counts. Compact endpoint receipts, script hashes, and control records are in [score2_chemistry_numeric_receipts.json](score2_chemistry_numeric_receipts.json). Their stage-specific `full_circuit_verified: false` flags are preserved as historical records of the numerical runs; the separately linked final full receipt establishes the accepted family's circuit result.

## Search scope and measured outcomes

The factorization has `R=8`, `B=143`, `C=44`, `N=76`, `brot=8` and batch size 5. The word table has shape `1220 × 75`: **91,500 eight-bit words, representing 732,000 logical bits**. Every search below changes the actual integer words. No acceptance decision uses a continuous angle inside a rounding cell.

| Search | Screened candidates | Exact shortlist | Measured conclusion |
|---|---:|---:|---|
| Single two-body word ±1, tag preserved | 167,413 | 1,500 | Individual error_2 improvements exist, but are tiny and do not by themselves satisfy the complete cost/accuracy contract. |
| Single-word least-squares weight transport | 167,307 eligible | 300 | A last-batch numerical PASS refit reaches lambda 46.9064877050; even a one-Toffoli patch would erase its gain. |
| Single one-body word ±1 | 10,526 | 300 | Address38/column21 frees 65.5464 µHa in error_1 before refit; its point-patch cost still outweighs the resulting lambda gain. |
| Free single-high 16-address LSB masks | 2,310 | 160 | The useful one-body block led to the verified identity refit; restoring that block's words showed the gain did not require the mask. |
| Free paired-high 20-address LSB masks | 3,010 | 200 | High0 XOR high76, column19, followed by refit gives the second numerical PASS endpoint. |
| Multi-row LS transport, final-batch columns70–74 | 365 | 17 | No new feasible contender. Best exact error_2 is 20.0001375303 mHa, above the limit. |

The first 210 one-body-only free-block masks are a subset of the 2,310 single-high masks, not an additional disjoint class. The bounded multi-row transport considered 76 supplied masks, skipped the three masks changing only one-body rows, and evaluated 73 × 5 actual word-table moves. It completed in 22.88 seconds rather than exhausting its 120-second budget. Its two leading endpoints were checked with the full official numerical evaluator. All measured processes stayed below **1492 MiB** peak resident memory with one BLAS thread.

The analytic shortlists are not proofs that all other word combinations fail. Nor do these finite local searches prove fixed-word optimality, global optimality, or that changing theta is necessary. Early point-screen records preserve provisional 20/40-Toffoli patch estimates used at that stage. Those estimates are not substituted for the later measured feature-patch resource counts.

## Mathematical contractions used in the search

### Exact one-word residual update

Represent a normalized projector `u u^T` in symmetric coordinates, multiplying each off-diagonal coordinate by `sqrt(2)`. This produces a length-2926 vector `v` and preserves Frobenius inner products. In each group, rows of `V` are these projectors and the represented coefficient rows are

\[
X=W^T V.
\]

For one changed feature `v_b → v_b+q`, define `s_b = (W W^T V)_b`, `κ_b = Σ_c W_bc²`, and the current full two-body residual `R`. The two-body tensor changes by

\[
\Delta H_2=q s_b^T+s_b q^T+\kappa_b q q^T.
\]

Consequently its squared error changes exactly by

\[
4q^T R s_b+2\kappa_bq^T Rq
+2\|s_b\|^2\|q\|^2+2(q^Ts_b)^2
+4\kappa_b\|q\|^2(q^Ts_b)+\kappa_b^2\|q\|^4.
\]

The inexpensive screen omits `2κ_b q^T R q` and bounds its magnitude by `2κ_b ||R||_F ||q||²`. Selected candidates include that term exactly. The word perturbations are finite, decoded integer changes; the residual formula is not a first-order angle approximation.

### Exact transport after a changed feature

A changed feature may be mostly represented by the other old feature rows. Simply holding `W` fixed can therefore exaggerate the unavoidable approximation loss. For one changed row, the code decomposes `q = c^T V + q_perp`, with `c = G^-1 Vq`, `G = V V^T`, and `μ = ||q_perp||²`. Setting `α=1+c_b`, `η=(G^-1)_bb` gives

\[
W_{\mathrm{new}}=W-
\frac{\alpha c+\mu G^{-1}e_b}{\alpha^2+\mu\eta}W_b.
\]

This is the exact least-squares weight transport for reproducing the old represented columns in the new span. It is not an optimization of the final chemistry score; that objective and the acceptance gates must still be evaluated.

The bounded extension handles 16- or 20-address masks. For every affected group it constructs the new integer-word feature matrix and solves

\[
W_{\mathrm{new}}=
(V_{\mathrm{new}}V_{\mathrm{new}}^T)^{-1}
V_{\mathrm{new}}V^T W.
\]

It uses Cholesky solves rather than explicitly inverting that matrix. The selected cases satisfy the normal equations to approximately `6e-16` maximum absolute residual. The identity offsets `d = H2_I − Σ_b W` are preserved by setting `H2_I_new = d + Σ_b W_new`.

### Exact residual update for the multi-row transport

Stack the old represented rows of affected groups into `X` and their changes into `Z`. Define `U=Z Z^T`, `A=Z X^T` and `G=X X^T`. Then

\[
\Delta H_2=X^TZ+Z^TX+Z^TZ,
\]

and the exact squared-error change is

\[
4\langle Z,XR\rangle+2\operatorname{tr}(ZRZ^T)
+2\operatorname{tr}(UG)+2\operatorname{tr}(A^2)
+4\operatorname{tr}(AU)+\operatorname{tr}(U^2).
\]

For screening, the only omitted term has magnitude at most

\[
2\|R\|_F\sqrt{\operatorname{tr}(U^2)}.
\]

All these bounds are algebraic bounds evaluated in float64, **not interval-arithmetic certificates**. The code checks them against the selected exact updates, and the leading reported endpoints are independently checked against the unchanged full tensor evaluator. The final official gate remains separate from the screening proxy.

## Why some word masks cost no Toffoli

Ancilla's feature-space proof and root's span scan found 33 high-address indicator blocks already representable by the existing free feature interface. Toggling a word's LSB on all valid addresses of such a block can use CNOT fanout without introducing a new nonlinear product. The other 44 high blocks have one parity obstruction. Pairing one of those blocks with the final partial high76 block removes that obstruction. High76 contains only addresses1216–1219, so this produces a 20-word mask rather than 32 words.

All masks in this search flip bit0 only; the existing `bit6 XOR bit7` tags remain unchanged. Columns0–4 were excluded because their first-loader interface has different costs. The final family must still prove the forward and reverse reachable batch contracts, clean scratch, and all measurement-dependent phases. The numerical search does not treat these chained loaders as arbitrary-target XOR maps. See the independently maintained [score2_angle_report.md](score2_angle_report.md) and the specific full-verifier receipts for the implemented circuit proof and counts.

## Code and reproduction

The new owned code is `score2_chemistry_*.py`. The main routes are:

- `discrete_screen.py`, `transport_screen.py`, and `onebody_screen.py`: actual single-word changes and the single-row transport.
- `block_screen.py` and `feature_screen.py`: free single-high masks and supplied paired masks.
- `identity_refit.py`: 352-coordinate constrained `H2_I` optimization with `W` and the chosen integer table fixed; final acceptance uses exact unsmoothed official metrics.
- `revert_onebody_check.py` and `revert_all_check.py`: explicit control experiments preserving `W/H2_I`.
- `feature_transport.py`: bounded multi-row transport with progress checkpoints and exact shortlist validation.

Each name above has the `score2_chemistry_` prefix. The scripts require the existing `score_chemistry_fast_model.py`, `score_chemistry_identity_polish.py`, `inverse_v2_chemistry_refit.py`, and `inverse_v2_chemistry_screen.py`. The manifest records their hashes. The measured runtime was Python3.12.14, NumPy2.3.5 and SciPy1.17.0, with `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1`.

The source baseline is the parent directory's `dqi_inputs/chemistry_4033/submission_asterios_full.npz`, SHA-256 `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`. The official verifier package is expected under the parent directory's `official_sources/Inzainos/verifiers`. Its packaged FCIDUMP and fixed shifts are checked by their official checksum gates; the search never substitutes a different Hamiltonian.

The retained original-word path can be reproduced from the repository with:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_block_screen.py \
  --out /tmp/gvqcc_score2/onebody_blocks --onebody-only --free-only \
  --shortlist 100 --emit 6

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_identity_refit.py \
  --source /tmp/gvqcc_score2/onebody_blocks/candidate_00.npz \
  --out /tmp/gvqcc_score2/block_refit --added-toffoli 0 --seconds 80 --iterations 700

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_revert_onebody_check.py \
  --source /tmp/gvqcc_score2/block_refit/candidate.npz \
  --out /tmp/gvqcc_score2/original_words_control
```

The paired path and its complete-word control are:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_feature_screen.py \
  --patterns score2_chemistry_paired_tail_patterns.json \
  --out /tmp/gvqcc_score2/paired --shortlist 200 --emit 8

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_identity_refit.py \
  --source /tmp/gvqcc_score2/paired/candidate_00.npz \
  --out /tmp/gvqcc_score2/paired_refit --added-toffoli 0 --seconds 80 --iterations 700

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_revert_all_check.py \
  --source /tmp/gvqcc_score2/paired_refit/candidate.npz \
  --out /tmp/gvqcc_score2/paired_control
```

The bounded final transport experiment is:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score2_chemistry_feature_transport.py \
  --patterns score2_chemistry_free_transport_patterns.json \
  --out /tmp/gvqcc_score2/free_transport --seconds 120 \
  --columns 70,71,72,73,74 --shortlist 48 --emit 5
```

Wall-clock budgets, eigensystem rounding, and matching boundaries can change a local optimizer's trajectory. The receipts identify the actual reported endpoints; these commands do not promise byte-identical NPZ output on every platform. Rejected candidate NPZ files were not added to the repository. Their source paths and hashes remain in the receipts. The accepted family is packaged separately by root with the matching official verification receipt.
