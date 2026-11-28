# Cross-replay: exact #268 pole and #267 structured panel

These are fixed-input diagnostics, not scores or an official distribution.
No full repair is claimed.

* Exact w32 #268 (batch 157, lane 244 from #262's official run): reconstruct
  the published syndrome, original mask and seed using the pinned verifier.
  Replay the original mask, zero mask, all 384 true-support one-hot bits,
  256 off-support samples, and 64 mask-linearity pairs at each of two seeds.
  The frozen 316K donor, the submitted V110, and **exact reconstructed #266**
  all passed the panel. This is not the same failure inheritance as
  #249/#259/#262, and passing this case is not enough to select a decoder.
* Independently rebuilt #266 from its immutable source and exact donor.
  The delivered circuit matches the published
  SHA-256 `071453f46be0f6108a09edd5b7b1e34595d86ddfe49ed0c80f369f0a35f7a349`,
  width 900Q, 55,521,542 ops, 388,867 static paid.
* Exact published #267 affine-subspace panel (144 syndromes, 432 lanes):
  #266 has **96 value errors, 96 dirty-ancilla errors, 43 raw phase errors**.
  The same 96 lanes fail value and ancilla; phase errors overlap those
  failures. All zero-mask lanes pass; all 48 random + 48 one-hot lanes fail
  at weights 15–17 and 27–35. Thus #267 did not first introduce this
  structured-panel failure. The exact 316K donor and submitted V110 both
  have 249 value errors on this panel. None is correct overall.

## Existing homogeneous chart, with canonical reverse

If the chart is regular, ((N,D)→(D,(N+hD)/q)); at a pole, it is
((N,D)→(qD,N)). Let (U) be the first output. Then
**(U\bmod q=D\bmod q)** in both cases. Consequently the inverse can determine
its branch from the current residue, **not from (h=0)**. In the pole case
the canonical reverse is ((V,U/q)); division by the public monic (q)
is exact. Unlike multiplying both components by (q) in the stored
reverse representation, it introduces no cumulative factor or degree
growth. The residue equality assumes canonical, unscaled coordinates.
It is not true of arbitrary independently rescaled representations.

This reconstructs the exact #268 unpadded degrees (31,32) from its archived
heads and normalized terminal data, without a stored pole bit. Stress:
256 alternating repeated-quadratic paths and 3,048 exact forward/inverse
coefficient checks. The ordinary head is zero on all 1,524 regular steps
in that construction, so treating a zero head as a pole would be wrong.
Three local Lean 4.35.0 lemmas passed with warnings as errors; no native
canonical converter or width/gate budget is implied.

## Reproduction

* Pin #268 at `1a9261744409656f9b9b731c686fe7fa17f40013`,
  `research/dqi262_homogeneous/{captured_input,extract_witness}.json`.
* Pin #266 at `8e6cc269aab60ae533b9a0d62347494387e4197a` and follow
  `research/dqi263_rebase_hmr/README.md`. Pin #267's structured generator at
  `b224d1979a55502988c0b0520de252863c7353f3` under
  `research/dqi316k_central_lambda/verify_structured.py`.
* With KickMix 1.0.0, NumPy, the #261 CRT helper, and DQI verifier on
  `PYTHONPATH`: `python replay_extended.py captured_input.json out.json circuit.kmb`,
  `python pole_inverse.py fixture_directory pole_inverse_receipt.json`.

### Localization in the exact #266 source pipeline

Rebuilt native prefixes using the same #266 generator, then tested all
144 distinct structured syndromes. At the raw key and after pad
replacement, every extracted rational pair still gives the correct roots
and magnitudes (0/144 mismatches at both boundaries). At the input of the
existing phase scan, **48/144** pairs give the wrong root/magnitude map
using the actual scan denominator \(xU(x)M(x)\). Exactly those 48 syndromes
produced value errors for nonzero masks in the full tape. This locates an
upstream arithmetic defect in NewOuter/Finish, independently of phase
sampling and subsequent cleanup, not in the old extraction or pad change on
this cohort. An unfinished prefix can have unpaid HMR phase debt; its raw
phase is a diagnostic only.

For this check, copy the pinned #267 verify_structured.py to
verify_structured267.py and run p266_prefix_probe.py with the pinned #266
generator and #261 CRT modules configured. Run all three stages by default.

The observed Euclidean profile of the post-pad square-root halves
((B,A\bmod B)) **separates the two groups exactly**. All 48 failures have
maximum drop greater than 2 (3:8, 5:12, 7:4, 9:4, 11:4, 13:16). All 96
successes have maximum drop 1 (95) or 2 (1). This is the explicit validity
boundary of the upstream gap-2 converter on the panel, not a theorem about
every input. Comparing direct roots with the actual scan coefficients
also shows that merely changing the phase repayment cannot correct these
cases. The zero-mask branch skips the core and masks the defect.
