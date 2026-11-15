# Actual v27 chemistry: bounded rank and discrete-word continuation

## Outcome

**No new accepted chemistry improvement was obtained.** The latest accepted
chemistry remains the other thread's H2-only candidate, whose full 78,080-shot
PASS is recorded in `results/2026-11-15/outcome_next_candidate_kaggle.json`:
NPZ `82c285b14ebabdbea128f9a9abdf86c533035a30cec995f00116283c4c26ad1e`,
cost **294887987.4337159**, 4030 loader CCX/pass, total T=14722 and Q=427.
This experiment did not alter that candidate, any original circuit, any
`outcome_*` file, a verifier, or a submission. It did not submit to Kaggle.

The new experiment uses the **actual recovered v27 words**. Its source is not
the old 4033 table and not the v27 NPZ's stale word metadata. The raw uint8
table SHA256 is
`8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`.
The exported W SHA is `a5bd72e36df3e810a08d55b8520bb68f07434d0f83a9df58411c9b8d8b34e395`;
the accepted H2_I raw SHA is
`c999197f880fc14864ea295f0015821b1b6cf692f520a07bc2051f45c1626b38`.
The unchanged official numerical evaluator reproduced the accepted baseline
cost, both errors, Lambda, gap, and lambda_eff before optimization.

## Measured experiments

| Stage | Actual integer-word changes | error2 (mHa) | Result |
|---|---:|---:|---|
| Accepted v27/H2 baseline, C44 | 0 | 19.9999880524 | Existing full PASS |
| C43, remove each group's smallest whitened singular component | 0 | 21.8489908443 | Fails |
| C43, 30-second whitened W refit | 0 | 21.1260501795 | Fails |
| Best single word with exact LS transport: address1145, column35, 59→61 | 1 | 21.1249799631 | Fails |
| Joint 12-word changes with simultaneous LS transport | 12 | 21.1198003041 | Fails |
| Joint candidate after another 30-second W refit | 12 | **21.1181258809** | **Fails** |

The integer screen considered steps ±1, ±2, ±4, and ±8, retaining tag-preserving
changes outside the initial batch. It screened **583,676** eligible moves and
evaluated **100** shortlisted moves using exact residual-update formulas.
The leading two cases were independently evaluated with the unchanged official
numerical evaluator. Its completed receipt is `score5_chem_v27_word_screen.json`.
No score hash, verifier salt, or sampling seed was selected or optimized.

The final joint candidate has error1 **33.3688415199 mHa**, Lambda
**297.5774799817**, gap **4.10234687848**, and lambda_eff **49.2412717373**.
It fails both error conditions. H2-only restoration was not attempted because
H2_I cannot repair error2. No new KMB family or full-circuit verification was
started for this numerically rejected point.

The direct effect of the 12 simultaneous word changes plus LS transport is
the change from 21.1260501795 to 21.1198003041 mHa. The subsequent W-refit gain
includes additional optimization time; it is not attributed exclusively to
the changed words. These finite local results do not prove that C43, different
integer words, or a larger joint search is impossible.

## Correct resource accounting

The official `SpinFreeData_V1` formulas give C43 **T=14644, Q=427** when the
same 4030-per-pass loader family is reused. Thus the rank change saves 78 task
Toffoli before angle patches. The 303 inner temporary qubits come from the
official resource model; there is no submitted circuit interface permitting
their arbitrary reduction. The separate ANGLE circuit cap remains 128.

The selected 12 changes have a **conditional** additional cost of 74 task
Toffoli under the old 4033 family's proved feature interface. That would give
T=14718 and Q=427, a net saving of only four task Toffoli. The actual v27 KMB
files were not available locally, so equality of that feature interface was
not verified and this is **not an executable measured resource result**.
The independent generic sparse-patch estimator instead gives **372** extra
task Toffoli for these same changes. Both counts are retained in the joint
receipt. No low-cost resource claim is made by assuming that the source
4030 circuits share an uninspected implementation detail.

The original C43 probe used the SVD factor gauge, which can increase the
absolute-value Lambda objective despite leaving its two-body tensor unchanged.
Before the joint experiment, the factors and H2_I were rotated together into
the near-original Householder gauge. The extended Gram matrix residual was
**1.42e-14**. This fixes that coordinate choice without changing the represented
one- or two-body tensors; it is not itself claimed as an accepted score gain.

## Numerical verification and limits

For every group, the fixed-angle feature matrix is whitened as V=LQ,
QQ^T=I, Y=L^T W. The exact squared residual is expanded about the current
candidate, and the gradient is `4 (A + K deltaP) Y`. The first directional
derivative check had scaled error **1.77e-10**; the joint check was
**8.83e-11**. The first Q-orthogonality residual was **2.92e-13**.

All changes in a group are transported simultaneously using
`Wnew=(Vnew Vnew^T)^(-1) Vnew Vold^T Wold`, solved by Cholesky rather than an
explicit inverse. Its normal-equation residual was **7.77e-16**. Each final
error2 was checked against a fresh official numerical evaluation within
1e-9 Ha. The final table has exactly 12 changed integer words, with every
bit6 XOR bit7 tag preserved. No continuous-theta value is substituted for
the rounded integer-word evaluation.

The two bounded refits used approximately 1.02 GiB peak RSS each. The
eight-step word screen used 1927.96 MiB and completed in 59.26 seconds.
The first rank refit used 869 objective calls; the joint refit used 1158.

The actual v27 table also cannot be obtained by merely replacing the output
XOR fanouts of the old 4033 per-batch product dictionary: the exact valid-domain
membership screen found missing output functions in each batch1–14. Batch0
words match the old source. This small screen is a restriction of that
dictionary, not a lower bound on a new loader synthesis. No additional tensor
random walk, general optimality claim, or small-cone contraction was made.

## Reproduction

Use Python with NumPy and SciPy and the project's pinned official chemistry
inputs at `../official_sources/Inzainos/verifiers/`. The KickMix-only virtual
environment does not include SciPy. Choose fresh output directories.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python score5_chem_v27_rank.py \
  --out /tmp/score5_v27_rank --seconds 30

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python score3_chemistry_multistep_transport.py \
  --source /tmp/score5_v27_rank/candidate.npz --out /tmp/score5_v27_words \
  --steps=-8,-4,-2,-1,1,2,4,8 --error-only --shortlist 100 --emit 2

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python score5_chem_joint_words.py \
  --source /tmp/score5_v27_rank/candidate.npz \
  --original-c44 /tmp/score5_v27_rank/baseline_actual.npz \
  --screen /tmp/score5_v27_words/transport.json \
  --out /tmp/score5_v27_joint --seconds 30 --max-changes 20 --max-added-t 76
```

The time budgets can change iteration endpoints on another machine; the
saved receipts, hashes, and exact final numeric checks establish this run.
The source angle table, weights, H2 patch, and geometry are all pinned by the
drivers. The rejected large NPZ checkpoints remain in the scratch experiment
directory; the repository retains the compact authoritative receipts and
12-word change list.
