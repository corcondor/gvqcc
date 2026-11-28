# Lower-paid half-degree phase stage, not a syndrome decoder

Reuses exact #246 input/output ABI and 851Q width. Replaces small polynomial
products in H-to-V and inverse, never the 4,095-point root test. No host
selection and no input-dependent gates in the changed magnitude region.

- Quotient: solve each left block, update the next block, solve that block.
  For each cross update the required coefficients are in the middle
  `m-1 .. n-2` of a product of length-m and length-(n-1) polynomials.
  Evaluate on a multiplicative subgroup of odd size L >= n-1. Cyclic aliasing
  only lands below the required middle. Dynamic programming chooses the
  split (physical linear cost not part of that first objective).
- The two non-overlapping low convolutions use degree-32 Lagrange
  interpolation at 33 fixed field points, emitting only the needed output
  coefficients. The upper-triangular odd-stride update uses parity-separated
  middle products and processes targets before changing source words.
- For each rank-one term, evaluation into existing source anchors and the
  corresponding output basis shear are reversible. Output can be dirty.
  Keep those frames between terms by applying coefficient differences;
  restore both at the block end. No additional wires. Lean here covers
  indexing and one retained-shear identity, not field interpolation or a
  whole-circuit equivalence theorem.

Original phase stage: 94,017 static paid, 3,900,081 instructions.
Main spectral phase stage: 65,457 static CCX/paid, 4,165,855 instructions
(after retained frames, from 4,739,301). All 28,560 saved paid ops are CCX.
There is a 265,774 instruction increase relative to #246; no time improvement
claim. H-to-V alone is 24,486 -> 10,206 CCX, with half-stage width unchanged.
The 45,045-CCX root chain is untouched. The complete stage agrees on values,
scratch, masks and phase in native KickMix. It still consumes D,H rather
than a raw 70-word syndrome.

The isolated arithmetic budget now changes: #261 key pair 220,343, plus
65,457 for this phase stage, plus 6,144 for explicit shared reciprocal
normalization, totals 291,944 before any native half-coordinate adapter.
A static 316,000 target leaves 24,056 for the rest. This is planning only:
no native splice, verified physical lifetime composition, updated score
or submission. Do not spend the margin twice if comparing adapter choices.

Reproduction: build exact #246 by its own README and retain the two original
binaries. From that build directory copy quotient_spectral.cpp.inc and
gen_spectral.py. Run `python gen_spectral.py transport`, compile
half_spectral.cpp with C++17, run its forward and half modes and use
finalize_spectral.py once on the emitted binaries. Test with pinned #246
verify_half.py, test_arbitrary.py, and stress_transport.py (which also
needs phase246/pivot_codec.py and #248 packed_cf.py). Frozen fixtures are
the existing #238 audit pack and exact V110 weight-33 witness.
