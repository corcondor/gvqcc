# Live-subspace ordering for the DQI adjoint product

The pinned e4 circuit's first unresolved central Q889 peak contains a GF24
adjoint consuming multiply at operation interval [18496027, 18502248).
The consuming operation holds all 24 old target bits and 24 new target
temporary bits until the swap and X-basis measurement of the old target.

The proposed separate encoding retained only the span of right parities
used by pending terms and the current output span of processed terms.
Linear basis changes would compile to CX, and measurement outcomes on the
old parity basis would be translated into the original 24-bit mask ABI by
classical XOR. Each rank-one term would still cost one Toffoli.

The exact group-order dynamic program and 10,000 individual term moves
kept the peak at 48 target plus temporary slots. This held for the installed
rank-99 tensor and the alternative 126-term quadratic construction.
The installed tensor consists of eleven 9-term groups, each of right
and output rank four.

The peak has a direct algebraic explanation. Let the next gate be the
first one that grows the output span to dimension 24. Choose a nonzero
linear functional that vanishes on all earlier output directions. The
underlying field product is surjective in the left argument whenever the
right argument is nonzero. Therefore the remaining right parities must
collectively have full rank 24. Otherwise a nonzero right argument would
annihilate every remaining term, and the selected output functional
would incorrectly evaluate to zero for all left arguments. The gate
needs the final output coordinate while all 24 input coordinates are
still available in this separate-storage model.

This bound applies to separate linear parity and output encodings. A
joint encoding can mix the old target and intermediate results, and a
chart-specific divide can replace the field product with another
factorization. This experiment produced no changed KMB or verifier run.
