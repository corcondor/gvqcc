# Exact lower cutoff cannot use a smaller fixed binary-linear projection

On any fixed set of 52 distinct allowed points, consider the 624-bit GF(4096) amplitude vector. The 52 ghost-filtered moments give an invertible linear map on that space: the Vandermonde matrix is square and every diagonal multiplier xG(x) is nonzero. The same proof applies if a fixed binary-linear probe reads the original syndrome instead of the filtered moments.

Any binary-linear map of rank less than 624 therefore has a nonzero kernel difference supported on some s in 1..52 points. Construct two legal words with that difference:

- s<18: add a common disjoint support of 18−s points; use no other points on the low side and all s on the high side.
- 18≤s≤35: use weights 0 and s.
- 36≤s≤52: partition into supports of s−35 and 35 points, with the original nonzero coefficients on each side.

The low side always has weight <=17 and the high side 18..35, yet the linear observations are identical. This is a rank lower bound on **fixed linear observations followed by any decision rule**, not a bound on work qubits, nonlinear inputs, or paid gates. It does not rule out streaming/structured recurrence or fusing the decision into a decoder.

`linear_probe.py` tests all 52 possible kernel support sizes and 12 independently chosen random 623-bit binary projections. `admission.py` checks 360 other legal cases and the 19-weight square-rank failure plus 17/35 same-51-prefix pair. The early Berlekamp–Massey exit is an **unpriced classical** comparison to the rectangular guard. On the 35-root witness it cannot exit until moment 52. No replacement emitted. Files from the pinned #332 source archive required: direct_codec.py and verify_submission_dqi.py; pinned KickMix 1.0.0 for native use. The Exact8 input KMB digest is e8a7ab1fe7132ecc7ecda70e33347e511eea5b4a386433ccbad844e8084e11c8.

Lean formalizes the support-count part in LinearProbeBound.lean; the binary-linear dimension argument and allowed-point mapping above are separate. FilteredRankAdmission.lean contains a lexical fix to the existing #334 proof (deprecated condition names replaced by simp of hypotheses), not claimed compiled locally. No main merge or competition change.
