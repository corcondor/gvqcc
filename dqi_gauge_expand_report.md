# DQI adaptive gauge expansion

This candidate expands the existing classical gauge selector from 64 labels to 128. It preserves the decoder body, the 889-qubit allocation and the existing field arithmetic. It is combined with an independently proved 96-Toffoli peephole reduction.

## Candidate identity

| Circuit | SHA-256 |
|---|---|
| Public baseline | `821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3` |
| 96-Toffoli reduction only | `5103812020bc0d6c4db32900777521479f01dfcca8dfd21ed74e9211770f389c` |
| 96-Toffoli reduction and 128-label gauge | `aafed8b0fa2bbfde21f47672a5e548a84a6d42d735e800557efbb2c04c310f09` |

The combined candidate has 59,378,482 instructions, 889 qubits, 154,799 classical bits and 383,318 static Toffoli-like gates. The binary is 496,087,939 bytes. Its reaction depth remains 40,891 in the native verifier.

## Why the gauge can save gates

The original circuit transforms the measurement masks so that 69 selected physical field points are fixed at zero. One remaining classical gauge parameter shifts the 4,025 normalized residual masks and a virtual pivot. A zero mask lets the decoder omit the corresponding quantum phase calculation.

The existing selector considers labels 0 through 63. The replacement considers these same labels first, then labels 64 through 127. Both use counts saturated at seven and replace the incumbent only on a strictly larger count.

This selection rule is monotone in the exact number of zero masks. If a new label wins, its saturated count is strictly larger. The incumbent count must therefore be below seven, so the new label's exact count is also larger. If no new label wins, the original selection remains. Saturation and ties cannot turn a better original label into a worse selection.

The seventh label bit is included in all mask shifts, syndrome phase compensation and closing operations. The retained pivot remains a 12-bit classical word. Temporary selector storage is allocated above the original circuit's classical-bit range, and its selected value is copied to the original pivot IDs. This avoids aliasing the decoder's measurement records.

The added selector work is entirely classical. Its peak temporary storage is 642 bits and its emitted quantum Toffoli count is zero. The expanded histogram uses 12,880,000 classical instructions. The decoder's existing arithmetic and measurements are not rewritten by this change.

## Verification evidence

The standalone selector was checked in the native Kickmix simulator on 203 fixtures, including a forced winner for each of the 128 labels, saturation cases, ties, extreme masks and random masks. All selected labels matched an independent integer oracle. Input masks were preserved and all temporary bits were cleared. A discrete check covered all 16,212,702 possible incumbent/replacement exact-count pairs relevant to the monotonicity argument.

Before replacing the opening and closing gauge instructions, the original generated pieces were compared with the downloaded baseline. All ten binary operation columns matched exactly. The splice then preserved the decoder body byte for byte, apart from the separately validated 96-Toffoli optimization.

The whole-circuit 256-shot smoke used the same seed, `20261114`, for all three circuits:

| Circuit | Mean Toffoli-like count | Reduction from baseline | Value errors | Phase errors |
|---|---:|---:|---:|---:|
| Public baseline | 382,598.671875 | 0 | 0 | 0 |
| 96-Toffoli reduction | 382,502.671875 | 96 | 0 | 0 |
| Combined candidate | 382,498.84765625 | 99.82421875 | 0 | 0 |

The smoke uses `log2_delta=-8`; its numerical cost is not an official-confidence competition score.

The combined candidate subsequently passed the default 102,400-shot verifier with one value error and zero phase errors. Its mean Toffoli-like count was **382,499.49657226563**, repetition overhead **1.1967314991687559**, and measured local cost **361,768,802,303.6398**. Runtime was 326.89 seconds with one worker, with peak resident memory 4,753,116 KiB. These are the actual measured results, including the failure.

That default local cost is worse than the baseline's published zero-failure cost of 360,209,905,486.0156. The failure raises the statistical repetition overhead enough to exceed the small gate saving. The two default runs use different random samples because the verifier derives its seed from the circuit hash.

To diagnose the failure, batches 345 through 349 were replayed with their exact original input and simulator seeds against both the unchanged baseline and the candidate. All 1,280 output syndromes, ancilla states and phases matched exactly. Both circuits fail the same absolute shot, 89,465, with sampled error weight 33. Thus the observed failure was already present in the unchanged baseline.

The unchanged baseline was then evaluated on the complete same 102,400-shot test set. Both circuits passed with exactly the same one value error and zero phase errors:

| Same-input full comparison | Unchanged baseline | Combined candidate |
|---|---:|---:|
| Mean Toffoli-like count | 382,599.91934570315 | 382,499.49657226563 |
| Value errors / phase errors | 1 / 0 | 1 / 0 |
| Repetition overhead | 1.1967314991687559 | 1.1967314991687559 |
| Local resource cost | 361,863,782,367.1329 | 361,768,802,303.6398 |
| Quantum bits | 889 | 889 |

On the identical test set the candidate saves **100.42277343752 Toffoli-like gates per shot**, of which 96 come from the exact peephole transformation and approximately 4.42277 from the gauge change. Resource cost falls by **0.02624746%**. The same-input baseline run took 324.07 seconds with one worker. No alternate salt or circuit-hash search was performed.

The repository includes the flat reports `dqi_combined_full_verification.json` and `dqi_baseline_paired_verification.json`, the selector checks in `dqi_gauge_selector_verification.json`, and the comparison with the exact failure-replay summary in `dqi_gauge_expand_results.json`. A successful local verification does not establish a Kaggle leaderboard result, and a reduction in Toffoli count must not be reported as an already confirmed leaderboard increase.

## Reproduction

Use the supplied original Syed source tree without modifying its certificates. Generate new pieces with:

```bash
python dqi_gauge_expand.py --source-root SOURCE/src --out-dir gauge128 --labels 128
python dqi_gauge_expand_verify.py --source-root SOURCE/src --labels 128 --output selector_verify.json
```

Use `kmb_splice.py` to perform the exact original-piece comparison and splice the new pieces, following its command-line help. Preserve the original register metadata and update the maximum classical-bit count. Do not substitute a different baseline or reuse an old correctness certificate for the result.

Run the competition verifier with:

```bash
python verify_dqi_candidate.py 821_ccx_gauge128.kmb \
  --verifier verify_submission_dqi.py \
  --output 821_ccx_gauge128_full102400.json
```

The runner uses the verifier's default sample count, confidence bound, seed derived from the new circuit hash, and empty salt. It uses one worker to limit memory. Its progress callback only records unchanged verifier task results. The report includes engine and verifier hashes, versions, elapsed time and peak resident memory.

## Provenance

The original adaptive gauge was written by Syed Asad Ali and released under Apache-2.0. The expanded selector is derived from `controller_work/after_v3/k24/adaptive_gauge/adaptive_gauge64.py`. The public decoder also incorporates Ertuğrul Özer's extractor-cutoff idea and Areeb Ali's cutoff-18 build with 241 retained products.

The verifier used here hashes to `f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`, matching the verifier pin in the source release. The installed engine is the official PyPI distribution `kickmix==1.0.0` for Python 3.12; its binary hashes to `d965e0ad42e7e3a147d4b28d6971a517f772dd79795cfc364be2fe9ffe3a7b80`. This engine binary differs from the original Python 3.13 wheel, so engine provenance is stated explicitly instead of reusing the original engine certificate.
