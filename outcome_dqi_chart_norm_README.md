# Qualified projective-chart patch and offline Kaggle worker

Candidate DQI SHA-256: `ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e`. Q889, static maximum382920.
Official default102400-shot result: PASS; value errors0; phase errors0; mean Toffoli382092.55653320; cost359731797766.29932.

The included worker is self-contained Python standard library only. It embeds the87KB exact byte patch, public-v27 member pins, proof hash, and the completed qualification. No full500MB KMB is needed in Git.

## Kaggle inputs

Attach outputs from:

- `maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry`, public-v27 v3 / script369706978, or an exact copy. The17 non-DQI members must match all pinned sizes and hashes.
- `geocpuresearch/gvqcc-exact4096-gauge-score2` v1 / script369719696, or another output containing the exact9a82 DQI.

Run `outcome_dqi_chart_norm_worker.py` as a CPU Python notebook/script. It discovers those pinned files under `/kaggle/input` and writes `/kaggle/working/submission.zip`, a packaging receipt, qualification, proof, and source notices. It never submits to the competition and never accesses credentials or the network.

For explicit local paths:

```bash
python outcome_dqi_chart_norm_worker.py --public /path/to/public_v27.zip --dqi /path/to/donor_9a82.zip --output-root /path/to/new_output
```

To reconstruct just the KMB:

```bash
python outcome_dqi_chart_norm_worker.py --patch-only --dqi /path/to/donor_9a82.kmb --output-root /path/to/new_output
```

The output folder must not already contain the target artifact. The script requires the whole pinned input SHA, each old patch region, and the whole reconstructed output SHA. It preserves the other17 public-v27 members byte-for-byte and rejects older chemistry portfolios.

## Scope

This generally repairs zero denominator at the third public pivot when its numerator is nonzero. The knownweight33 counterexample is fixed. A knownweight31 numerator-zero failure remains. The original and new circuits were compared on the same16384 independent valid inputs, with no new failures. A finite verification PASS is not universal correctness or a new Public score.

The source builders in this bundle are optional research provenance and require the pinned upstream DQI source/KickMix environment. The portable worker itself has no such dependencies. See the proof, component receipt, splice ownership audit, paired receipt, and qualification for evidence.

The bundle retains the upstream Apache-2.0 license and source credits. The candidate is for review and the next submission quota slot.
