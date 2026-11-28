# Native scale covariance separates the #257/#279 return defects

Replayed the exact archived 622 inputs on the low-cost #257 and #279
tapes, with fixed nonzero scales 1, 2, and 4 and the same syndrome, mask
and measurement seed for each conjugate. No per-input chart selection.
Both baseline tapes give identical lane-resolved receipts across all
three scales. The #279 comparator here is the hash-pinned CI tape with
67,549,292 instructions, not the nearby #283 variant.

Independently compiled #291's actual full #279 wrapper, reproducing
SHA-256 d014eaedd988919981ad971ff6131e6e810d0ff39541b601f417d2183af9aa06
exactly (900Q, 318,333 static paid; 4,361 affine gates each way).
The serialized wrapper matched an independently computed host-frame
reference on **all 622** lanes, including all 840 returned value bits,
phase, ancillas, all mask bits and paid counts.

| Base residual | Native at scale 2 | Native at scale 4 | Distinct lanes |
|---|---|---|---:|
| None | None | None | 170 |
| Chart product, repeated | Same internal chart factors | Same internal chart factors | 174 |
| Single chart factor, kappa=3169 | None | None | 25 |
| Complexity 35, not chart product | Complexity 35 | Complexity 35 | 153 |
| Complexity 35, not chart product | None | None | 20 |
| Complexity >35 | Complexity >35 | Complexity >35 | 80 |

Value errors 452→407 at both nonidentity scales. Raw phase errors
233→225 (scale 2) or 211 (scale 4); four phase-only failures remain in
each case. Seed-different original #291 results are not overwritten.
These are diagnostic samples, not an ordinary reference-rate estimate.

For a monic recurrence L of degree d, scaling the moment with index j by
alpha^(j+1) changes L to alpha^d L(X/alpha). The reverse scales its chart
factors back. On **all 174** persistent repeated-chart lanes, the internal
polynomial factors and multiplicities stay identical for scales 1, 2, 4,
while the outer factors move off the normalized chart family at both
nonidentity scales. The 1,026 nonzero recurrences of degree at most 35
(per one baseline tape across its three arms) all satisfy the exact
coefficient transport assertion. Quadratic and squared-quadratic
transport and the pointwise term identity passed strict Lean 4.35.0.

This locates a family in the decoder's internal chart rather than the
physical root coordinates. It does not locate the first instruction,
explain the remaining 233 persistent generic residuals, or repair those
174 by changing the fixed chart. A uniform nonzero scale is a permutation
of the stated ordinary support/mask law, so this archive improvement and
the small paired paid differences cannot be promoted as expected
savings. No full recovery, score, deployment or submission.

## Reproduce

Use KickMix 1.0.0, the pinned official DQI verifier, and the prior
paired257 Python modules on PYTHONPATH. Archive: the same
GVQCC_316K_RANK15_FULL_SPLICE_SOURCE_RECEIPTS.zip and saved.bin as paired257.
Use exact #257 Actions artifact 15253960748 and #279 artifact 15254190741.
Use #291 scale_conjugate.cpp and native.hpp at
4b0effc4bba721b7078ebb664f14cfe11f6b80ae.
```sh
python scaled.py exact257.kmb archive.zip result257.json
python scaled.py exact279.kmb archive.zip result279.json
g++ -O3 -std=c++17 scale_conjugate.cpp -o wrap
python frame.py exact279.kmb f279.ops
./wrap exact279.kmb f279.ops scale279.kmb
python scaled.py scale279.kmb archive.zip result_wrapper279.json --exponents 0
python compare_wrapper.py exact279.kmb scale279.kmb archive.zip wrapper_equality.json
python summarize.py
lean -DwarningAsError=true ScaleChart.lean
```
