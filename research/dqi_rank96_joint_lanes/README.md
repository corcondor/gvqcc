# GF4 whole-tape continuation, research only

Exact low-cost comparison remains 316094.00 matched #323 full KMB,
54817e9385f24940585f5a391025152d4a65a36381887ca77b7bab61413ea2ec.
No <=97 witness exists in #327. Do not report 96 or 97 without proof.

- 540000 proposals on shared-right GF64 two/three lanes and truncated
  cubic two-lane map; best 10, 15, 10 GF4 products, no gain.
- Exact projective coset scan over triple spans of four seeds and 1024
  invertible multiplication isotopies: 242145 candidate-form entries,
  61870 elimination trials; best33. Not an exhaustive GF4 projective
  search and not a global rank bound.
- Mixed-control quadratic search over GF4, rather than GF2: 240000
  proposals; alternating wedge pooling, proportional output group
  decomposition and exact coefficient checks, best33. One dual-number
  witness has six mixed planes and eleven nonzero GF4 square corrections.
  Squaring is binary-linear, so exact binary expansion costs 99 CCX
  and can be compiled without new qubits. No <=97 witness.
- First native all-tape run on exact accessible #279 (NOT #323):
  333/333 factor maps matched; 299 actual rewrites, 54 affine-sign
  sites found, 67549292 -> 69355945 instructions, 318333 static paid,
  900Q, paired full-output digests and paid unchanged. CI 46154876125.
  The later sparse pivot compiler removes the arbitrary 256-coordinate
  cap, and accepts generalized 48-bit mixed control pairs and linear
  repayment. Report its measured full receipts separately.
- --strict97 refuses existing witnesses; --dry99 is not a score gain.
  The manual workflow accepts exact #323 KMB from a known Actions
  artifact only after SHA256 verification. Local container ClientError
  prevents reading the current library KMB. Do not conflate #279
  diagnostic with actual #323 316094 full tape. No submission or merge.
