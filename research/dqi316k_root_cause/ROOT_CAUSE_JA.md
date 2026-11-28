# 316k / 900Q root-cause audit (2026-11-28 JST, NOT SUBMISSION)

Owner directive: retain 900Q allowance; correctness first, then paid/CCX reductions.
Do not substitute the expensive narrow branch or count externally selected charts
as a repaired native oracle. No merge or Kaggle submission.

## Current evidence across branches
* #208: old 900Q exact 4b572141... donor and its exact compact PA001 parent
  show 272 value failures / 576 zero-mask stratified shots; errors at weights
  1..17. Their output vectors match, so the four later D16 substitutions
  are not the cause of these particular failures.
* #210: fixed annihilator residuals exist empirically for several weights.
* #209/#221: fixed rotations fail on inverse-rotated counterexamples; the
  1244/1244 branch-external replay is not a single coherent repaired circuit.
* #225: exact inverse block replacement remains erroneous on whole-circuit
  forced weights (parent 122 value + 4 disjoint phase errors; replacement
  122 value + 5 disjoint phase errors). Do not confuse local equivalence
  with decoder repair.
* #219/#223: narrower 897/896Q branches pass sampled regression, but much
  higher paid cost and not universal proofs. #223 official attempts
  memory-limited. No repaired 316k binary found in reviewed latest PRs.

## Fresh paired zero-mask / one-hot probe
Pinned old SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52,
900Q, 69782188 instructions. Repaired reference V127 SHA256
3b5948dd59ac064f56e92ae6143bd4dccf4aa17a912dc2f76862885e2600217f,
898Q, 50198040 instructions. Native KickMix 1.0.0, official register
validator and finite-field tables, synthetic legal supports at weights
0,1,2,6,17,18,35, fixed RNG 202611280337, measurement seed 202611280338.
For each support's first/last and one off-support location (deduplicated),
probe all 12 mask bits. Each candidate runs 216 zero-mask + 216 one-hot
shots. Not the official verifier. Counts are probes, not distinct syndromes.

| metric | old | V127 |
|---|---:|---:|
| zero-mask syndrome restoration errors |132|0|
| one-hot syndrome restoration errors |132|0|
| zero-mask global phase errors |81|0|
| paired XOR phase vs target one-hot coefficient |19|0|
| output syndrome depends on mask in paired test |0|0|
| dirty workspace or mask-restoration errors |0|0|

**Zero mask is decisive:** target phase is always +1 regardless of input.
Consequently a nonzero phase flag at zero mask is a separate violation,
not explained by an incorrect decoded magnitude alone. Example weight 0:
9/12 zero-mask shots flip phase even though syndrome restoration is
correct. Same seed does not by itself prove equal internal HMR histories;
paired phase differences are diagnostic, not a formal isolation of the
scan or proof of a recovered error word. For weights 1,2,17, the probed
phase differences agree with expected magnitudes despite corrupt output.
For weight 6, positions 1399 and 3155 return differential words 0 instead
of 3263 and 120, while position 0 returns 1834 instead of 0. Do not infer
a single failing physical gate from these endpoint tests.

## Finite-field analysis of new witnesses
Berlekamp-Massey on the native syndrome output, with independent check of
every recurrence equation in the available 70-word sequence:
| weight | changed words | changed bits | output linear complexity | residual complexity |
|---:|---:|---:|---:|---:|
|0|0|0|0|0|
|1|70|416|37|36|
|2|70|420|36|36|
|6|70|400|35|35|
|17|70|419|21|4|
|18|0|0|18|0|
|35|0|0|35|0|

Output complexities >35 at weights 1 and 2 rule out any legal
<=35-sparse interpretation of those returned 70 words. The weight17
residual has exact characteristic polynomial
F(X)=(X^2+X+3431)^2=X^4+X^2+2837 (GF(4096), 0x1053).
All 66 available recurrence equalities checked; F nonzero at all 4096
base-field elements. This independently reproduces #210's structural
residual observation, not a universal formula for all low weights.
The residual filter was applied to the *corrupt* output only. 66 filtered
moments, classical Hankel solve, recurrence extension to 70 words and
division of each recovered magnitude by F(a) recover the entire original
syndrome exactly for this new w17 witness. The original syndrome was used
only for final comparison. **Not a KMB repair:** the choice of filter and
coherent reconstruction, phase repayment, inverse interface and other
weights remain open.

## Mathematical obligations / prioritized repair
1. Reject the cutoff/finite-chart assumption on low weights and zero
   residues; #208's cutoff17 pattern is evidence, not a proven first bad
   gate. Recover old physical extraction chart and phase witnesses from
   archived KMX; distinguish forward extraction, scan and inverse extraction.
2. Restore the total map, including termination and poles, with actual
   two-sided inverse on reachable encoded states. A post-hoc value filter
   is insufficient, as the zero-mask phase counterexample proves.
3. Preserve 900Q bound, retain original arithmetic wherever proven exact.
   Use #182 polynomial degree and unique syndrome facts, #210 annihilator,
   #221 parser stability, #225 inverse-basis and phase certificate.
4. Require the single unwrapped full KMB to pass all saved regressions
   (including matched moment windows, inverse rotation, forced weights,
   zero mask and one-hot mask probes), then unchanged official verification.
   No cost optimization is accepted as a correctness repair without that.
5. Distinguish static paid, CCX, and average executed paid on a matched
   official-distribution panel. Diagnostic panel averages are not scores.

Reproduce with phase_probe.py and the two exact archive KMBs. The companion
archive contains full JSON receipts, recurrence analyzer, classical recovery
script and previous 432-shot audit. No new native repaired 316k KMB, no
whole-circuit formal correctness proof, no official score claim.
