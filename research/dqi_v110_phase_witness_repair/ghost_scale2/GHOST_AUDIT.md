# The scale-2 locator seam: support loss vs. return fault

Research only. Raw files and archived probes are not included. No candidate was
submitted, and the selected #292/#294 bundle is unchanged.

## Exact source anchors

- #290 DQI in #292: SHA256 `2545a84896ba44152eab0db6856a056d23f60869c60fac8e7d1a8788c51e88dd`, cut 36,287,888.
- #294 DQI: SHA256 `b9f72a7bde001b81e0dc2530618dfa29815038b0bec7a542f75b2e3298d26870`, cut 57,227,861.
- The cut is unique on the 1,024 surrounding opcodes and quantum operands (classical IDs intentionally omitted). A prefix of the actual KMB, with any open classical scopes closed at EOF, was run under KickMix 1.0.0. The independent scalar bitsliced replay and native replay returned identical values for all 900 qubit lines in all 622 archived cases at the cut.
- At #294's cut the expected nonzero roots are twice the outer roots in GF(4096), not the unscaled or inverse-scaled roots. The monic polynomial in the outer frame is `P(2X)/2^35`.

## Results

On #296's 21 unsupported locator states, all 21 contain at least one irreducible factor of degree greater than two. The arbitrary-degree CRT projector reproduced all 70 physical trace moments for each of the 21 synthetic test payloads. This is not a decoder repair.

Exact outer nonzero support on the matched 622 archived cases: 465 with #290, 495 with #294, 127 with neither. All 127 misses lose every true root; archived weights 6, 8, 10, 12 and 16 realize this obstruction. No #294 miss contains all true roots plus extras. A 35-degree monic P with missing true roots cannot reproduce all 70 words by altering the weights of its roots: the union has at most 70 distinct nonzero elements, so the first |union| power moments are an invertible Vandermonde times a nonsingular diagonal. The recurrence-only test independently reproduced the same classification.

In fresh KickMix replay of the full pinned #294 KMB on this archive, 410/622 cases failed the union of restoration, phase, dirty-Q and mask checks. Of the 495 exact-support cases, 283 still failed (280 restoration, including 129 also with phase error, and 3 phase-only). All 127 missing-support cases failed restoration. This is an intentionally difficult archived panel, not an IID error-rate measurement.

## A mathematical bridge for the exact-support cases

Let `S_j = sum_x e_x x^(j+1)`, `R(X)=sum_j S_j X^(-j-1)`, and `N=(P R)_+`.
If all true roots are simple in P, `N(x)=e_x x P'(x)` for each nonzero physical root. This follows by writing `R=sum_x e_x x/(X+x)`. Higher-degree ghost factors need not be factored to form N. If P omits a true root the bridge must not be used. Recomputed raw-S amplitudes agree with independent GF(4096) canonical amplitudes on all 495 exact-support #294 cases. This tests a reference output, not the native amplitude coordinates or downstream HMR on a modified circuit.

The numerator is a truncated convolution of the reversed coefficients with the syndrome. For degree 35, remove the known monic term first. The remaining two length-34 factors have degree at most 33; interpolate their product on 67 distinct field points (595 naive variable products). `diagnose.py` checks the resulting #283-style bilinear form against the direct numerator. 67 is a field multiplication count for the reference numerator alone, not a CCX cost, and reversible scheduling and cleanup are unpriced. Apply #285/#287/#299 to the subsequent inverse/normalization and #293/#297 to HMR only after proving the native ABI; an upstream locator repair is still required for the 127 cases.

#298's 190,110 CCX D,N converter and #299's 183,642 CCX cache are component results. #299 reports 60 higher-confluent failures. Its separate 317,996 static-paid full DQI does not reduce executed paid relative to its own #295 fusion parent on the reported matched panel; the improvement vs. #292 already comes from the gauge. No verified full-oracle replacement or higher score.

## Reproduce

Use the common archive's `joint_work/audit/common.hpp`, `replay.cpp`, and
`saved.bin`, and extract the #296 archive into this directory. Run `bash run.sh`
with the pinned binaries named `old.kmb` and `new.kmb`; install the official DQI
verifier, Python 3.12, NumPy and KickMix 1.0.0 for the native calls. The two archive
inputs are referenced only by path; this directory contains no captured inputs.
