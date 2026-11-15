# Chemistry on the 27.32784499 baseline

The source is the score12 ZIP with SHA-256 `a339f391056756c72a9f3a994090d509d3bf38ebee94a075a6d68fe13f2bffea`. The original 15 ANGLE KMB files, DQI, and invsqrt are identical. The verifier received only new `W` and `H2_I`. The score12 ANGLE input contract counterexample is unaffected.

The fixed-word optimizer runs constrained proximal SQP with exact absolute values, a local Schur-complement constraint around three near-zero one-body eigenvalues, and an optional diagonal inverse curvature metric in the proximal least-squares and restoration steps. For the combined run, the same official verifier accepted 78,080 shots. The measured figures are:

| | Score12 | Metric continuation |
|---|---:|---:|
| Effective normalization | 46.90965323562981 | 46.90965125142687 |
| Toffoli, qubits | 14722, 427 | 14722, 427 |
| Chemistry cost | 294887871.6772202 | 294887859.20393723 |
| Total holding DQI and invsqrt fixed | 27.327844992124593 | 27.327845377432578 |

The official mapping digest for this run is `895f6b9d53bf148b4117b6281903573f2c95eedb34854c084d3dc075a73103b0`. This is a numerical improvement of 0.0000003853 in portfolio score.

## Public warm start and verified best

The Heliosli v56 reserve factorization has the same tree and byte-identical recovered angle words as score12. It verifies on the score12 ANGLE files with chemistry cost 294878860.57649696. A further 35-second constrained refit, followed by the 78,080-shot unmodified verifier, produced **294878855.8279802** at the same T, Q and ANGLE bytes. The derived portfolio score is **27.328123503355716** with the original score12 DQI and invsqrt. The official mapping digest is `955c24d39bcf7ec8df5628ed68a888dee9daeb48d450f75d9c678d206f5c4f9f`. Most of the gain comes from the public starting weights.

The starting weights are Heliosli's Apache-2.0 reserve snapshot, SHA-256 `f1888d7ad0533227fd5a373711cbaea2c82b6205ef785818c08e2a168414c491`, preserved by prvsiyan. Upstream credits cover arizalfirdaus123's v9 table, boristown's v6 weights and later refit, and prvsiyan's refit code. [Dataset manifest and source notices](https://www.kaggle.com/datasets/prvsiyan/vqcc-verified-best-of-circuits-1106a) · [Heliosli's original release](https://www.kaggle.com/datasets/heliosli/qcc-circuits-live)

For byte-exact replay, apply `public_weights_xor_patch.npz` with SHA-256 `18a602ffd49bd9ebdd141a078dffad29c0482b1aa288c3a482b83b2d6a09b557` using `stage.py --xor-patch` with the score12 ZIP and scorecard. This regenerates the verified factorization NPZ SHA-256 `d256b6089d4f4c51ea9bfbc49c072be56c02dc4db0e4da5faafd437e9f93c555`. To run the warm-start refit from scratch, use the pinned public NPZ as `--start` and flags `--label hard_public --seconds 35 --tight --schur --metric`.

## Normalization bound from the verifier

Write `d = H2_I - sum_b W`, let $h'$ be the one-body matrix, let $L=\|h'\|_*$, and set $a=E_{\mathrm{upper}}-E_{\mathrm{core}}+\eta\beta_1$. The score code fixes $a\simeq-559.1324731485038$. The triangle inequality yields
\[
\lambda_{H_2}=\frac14\sum_{rc}\left(\sum_b|W_{rbc}|+|\mathrm{H2\_I}_{rc}|\right)^2
\geq \frac14\|d\|_2^2.
\]
Since $g=a+L-\operatorname{tr}(h')+\|d\|_2^2/2$ and $\Lambda=L+\lambda_{H_2}$,
\[
2\Lambda-g \ge -a+L+\operatorname{tr}(h') \ge -a.
\]
The strict gap floor $g>3.914898$ implies $\lambda_{\mathrm{eff}}>\sqrt{3.914898\,(-a)}\simeq46.78617959$. The argument uses the official fixed shifts and is independent of the choice of angles, weights, or factorization rank. At score12's $T,Q$ and other component costs, the portfolio ceiling for changes to normalization alone is approximately **27.35186423**. Holding Q and the other Toffoli terms fixed, 28 would require at most **3,530 ANGLE Toffoli per pass**, even at the normalization lower bound.

For each group, put $A_r=[W_r;\mathrm{H2\_I}_r]$ and $P_r=A_r A_r^\top$. If $P_r$ is preserved, the one-body term, SOS gap and two-body tensor are preserved. Also $\lambda_{H_2}\ge\sum_r\|P_r\|_{1,\mathrm{entrywise}}/4$. On score12 the lower bound is 269.68099930 versus 269.82108852 measured, implying a tighter ceiling of approximately 27.33011596 at fixed resources and exact group Gram. The frame search `overcomplete.py` tested candidate directions at row sign changes and a uniform grid, via 7,568 small LPs. Increasing the number of columns gave no cost improvement in the screen.

## Reproduction

Use the unchanged official verifier, the Stage-12 baseline ZIP and JSON, and the baseline optimizer NPZ containing the recovered words. The numerical start's `W`, `H2_I`, and `tree_edges` must equal the originals in the baseline ZIP. The optimizer uses the recovered integer `angle_words` rather than the ZIP's convenience array. The fixed-angle evaluator dependency `chem_next_fixed_angles.py` is in the previous score12 folder.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export PYTHONPATH="$SCORE12_SOURCE_DIR:$VERIFIERS"
python chem_next_public4030_prox.py --start "$SCORE12_NUMERIC_WEIGHTS" \
  --label highest_cont --seconds 65 --tight --schur
python chem_next_public4030_prox.py \
  --start chem_next_public4030_highest_cont_candidate.npz \
  --label highest_metric --seconds 60 --tight --schur --metric
python stage.py "$SCORE12_ZIP" "$SCORE12_SCORECARD" \
  chem_next_public4030_highest_metric_candidate.npz family_metric
python "$VERIFIERS/dfthcsos/verify.py" family_metric > metric_official_verify.json
python normalization_bound.py "$SCORE12_NPZ" "$SCORE12_CHEMISTRY_RECEIPT" \
  "$SCORE12_SCORECARD" normalization_bound.json
```

The numerical run budgets are wall time. For exact replay use the verified
`weights_xor_patch.npz` with SHA-256
`d08b0a936e0d636310c9354f6475869f57358385cde340fa3b8f559bbb5d5e68`. Run
`python stage.py "$SCORE12_ZIP" "$SCORE12_SCORECARD" weights_xor_patch.npz family_metric --xor-patch`.
The resulting factorization NPZ has SHA-256
`83ac043944c3ade5d048bdfb80f144bbbd8df78fefc8c0f397797212e0003797`.
