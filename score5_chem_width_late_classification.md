# Late DQI width peaks: exact source classification

## Result and scope

The two nearby peaks at operation indices **26,458,417** and **26,460,853**
belong to one paired GF(2^12) division. The peak at **35,690,810** belongs to
a GF(2^24) adjoint consuming product. Both conclusions are exact opcode and
operand bindings under injective quantum/classical wire renaming, not pattern
similarity. No production circuit was changed, and no simulation or full
official verification was run for this audit.

The audited whole KMB is
`/workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/dqi.kmb`, SHA256
`6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02`.
Its actual bytes were independently hashed and agreed with its profile.
The source script, templates, maps, source-file hashes, and selected lifetime
intervals are recorded in `score5_chem_width_late_classification.json`.

These findings do **not** establish a smaller global quantum register. The
already generated six-bit chart replacement still leaves other peaks. The
whole-register header remains **889**, and those other peaks must be repaired
before reducing the header and running the final official verifier.

## Exact component bindings

All intervals below use zero-based operation indices with an exclusive end.
The surrounding implicit condition depth is zero for every listed block.

| Actual operation interval | Exact source component | Toffoli count | Relevant roles |
|---|---|---:|---|
| 26,456,255–26,463,192 | `gauge_park_paired.divide_prefix` | 149 | Factor q12–q23; targets q36–q47, then q0–q11 |
| 26,458,248–26,460,684 | `dual_scale.scale_word` | 42 | First target, reciprocal multiplier, preserved original factor |
| 26,460,684–26,463,120 | `dual_scale.scale_word` | 42 | Second target, same reciprocal and original factor |
| 35,689,634–35,695,903 | `direct_carry_arithmetic._adjoint_consume` | 99 | Source q816–q839; value q132–q143 followed by q72–q83 |

The first paired block is 6,937 operations: a 65-Toffoli compact reciprocal
and two 42-Toffoli consuming scalar multiplications. Its reciprocal is in
the ordered physical wires
`[880,881,879,888,877,882,885,869,865,867,866,871]`.
Each scalar multiplication uses a twelve-bit clean output, swaps it into the
target, measures the old target, and pays that measurement phase using the
updated target and the preserved original factor.

The paired source corresponds to the outer entry call
`paired_scale.divide_prefix(builder, [H, q], s)` in
`after_c5/converter_width/gauge_park_outer.py`. The exact bound helper is
`after_c5/converter_width/gauge_park_paired.py`; the caller identification is
supported by the source order and word roles. The inverse-mask interface is
preserved until the later paired multiplication.

At these two peaks the branch-sensitive conservative lifetime analysis has
49 active scratch intervals: the persistent 24-bit carry, a twelve-bit
reciprocal, twelve computed-output bits, and the live gauge flag. There is
no retained child norm in this paired division at the multiplication seam.
The earlier child-norm borrowing transformation therefore cannot simply be
copied to these wires.

Operation **26,481,000** itself has only **25** active scratch intervals in
this exact tape; it is not one of the peaks above. This distinction matters
when applying offsets from an older circuit.

The later adjoint block implements
`value ← conjugate(source) × value` and returns the old-value HMR mask. Its
source is restored exactly. The block has 6,269 operations and 99 Toffolis.
It allocates a full 24-bit computed output before the swap and measurement.
The 24-bit output, a live flag, and the persistent carry account for the
observed scratch peak. This is a different architecture from a tower inverse
with a redundant live norm. No claim is made that every equivalent adjoint
product must use this width.

## Concrete unadopted one-bit proposal for the paired division

The paired division has a narrower possible schedule using the existing
`GaugeCarrier` contract. This is a source derivation only: no replacement
KMB was emitted or simulated, and it is not included in the submitted
candidate.

Let `s` be the preserved unit factor, `r = 1/s`, and `f` the gauge flag.
The existing gauge contract is `f = 1 ⇒ other = 0`. Parking a known unit `s`
swaps it with `other` under `f`, so the parked physical `s` is zero exactly
when `f = 1`. The existing carrier can then HMR and lend the gauge wire,
later reconstruct `f` with a zero query, pay the HMR phase, and undo the swap.

The schedule is:

1. Compute the compact reciprocal with gauge borrowing disabled.
2. Park the preserved unit factor `s` using `GaugeCarrier.park(s)`.
3. Consume both target words using `r`, borrowing the clean gauge bit as one
   bit of the twelve-bit temporary. Retain the two old-target HMR masks.
4. Unpark, restoring `s`, `other`, and `f` exactly.
5. Repay each retained target mask using the restored factor and updated
   target. Then emit the original deferred reciprocal-mask interface.

The phase identity is exact on the unit-factor contract. If `y = x/s` and
the old target `x` was HMR'd with outcome mask `m`, its phase is
`(-1)^(m·x)`. After restoring `s`, the existing multiplication phase
`phase_product(y, s, m)` contributes that same sign because `ys = x`.
Its product parities and classically controlled CZs add no Toffolis.

This postponement is necessary: the original scalar routine reads `s` to
pay the target phase immediately, which would be invalid while `s` is
parked. The reciprocal remains live throughout, and the parking operation
does not change it.

The proposed additional Toffoli count is **35**: two twelve-bit controlled
swaps plus one twelve-bit zero predicate, `24 + 11`. At the consuming
products, borrowing one gauge bit changes twelve new temporary bits to
eleven. The reciprocal construction uses 22 scratch bits and the zero query
uses ten auxiliary bits, so neither creates a larger local peak in this
schedule. This is a proposed **one-bit local reduction**, not a measured
whole-circuit result.

Before adoption, the replacement still requires a native phase-aware
component check, exact allocation and lifetime mapping for its extra
classical masks, preservation of the original returned reciprocal-mask
IDs, and a new global interval check. Repairing this one paired division
would not remove the later 24-bit adjoint-product peaks.

## Reproduction

The script generates only four small source templates, matches them inside
two bounded windows of the immutable KMB, and records selected lifetime
intervals. It does not rebuild or simulate the full decoder.

```bash
MALLOC_ARENA_MAX=2 /workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python \
  score5_chem_width_classify.py \
  --input /workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/dqi.kmb \
  --profile /workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/profile.json \
  --intervals /workspace/scratch/3815fb5fae06/score5_dqi_width/branch_6a.tsv \
  --out /workspace/scratch/3815fb5fae06/score5_chem/width_classification
```

The observed classification run took 3.02 seconds. Template generation,
exact byte matching, and independent file hashing are the complete audit
scope. They establish where these implementations occur; they do not prove
that the proposed schedule has been integrated or that all other width
peaks can be removed.
