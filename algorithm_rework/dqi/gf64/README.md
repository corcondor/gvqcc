# Auxiliary-free scaling by a quantum GF(8) scalar

This experiment changes the algorithm for a generic nested GF(64) inverse.
It is separate from the matched GF24 inverse that reuses its child-norm bank.

For a nonzero norm `a`, reversibly replace its three polynomial-coordinate
bits by the exponent `e = -log_g(a) mod 7`. Multiplying a limb by
`g^e` then needs three controlled **constant linear maps**. Each map in
the selected GF(8) basis is emitted as three rank-one transvections, each
using one CCX and CNOT basis changes on the limb. The exponent is shared
by both limbs, then decoded to `inv0(a)`. The former three-bit product
register is gone. On the only norm-zero case used by the inverse, the
limbs are both zero, so the reserved exponent code also gives the correct
zero output. Temporary exponent coding uses no measurements.

The surrounding GF(64) inverse is the usual quadratic tower map
`(L,R) -> ((L+R)/N,R/N)`, with `N=L²+LR+δR²`. After scaling, the stored
reciprocal norm is the norm of the result, so the original measured norm
cleanup is exact. The new inverse can supply the baseline deferred-mask
ABI with zero-valued masks, since no inputs are erased during scaling.

| Native component | Clean helpers | Static Toffoli | Native shots |
|---|---:|---:|---:|
| Standalone quantum GF(8) scaler, including norm inversion | 0 | 14 | 456 |
| Baseline nested GF(64) deferred inverse | 6 | 21 | 512 |
| Exponent-coded GF(64) inverse | 3 | 29 | 512 |

The scale test covers all 56 pairs with a nonzero scalar and the
zero/zero pair. Inverse tests cover every GF(64) input under eight
measurement seeds, with all output bits, cleanup and exact phase probes
checked. A common, separate six-bit input witness in both inverse fixtures
closes baseline measurement debt and confirms witness restoration; the
helper columns exclude that witness.

This is a local width/Toffoli tradeoff. A later six-bit half-scale is a
separate width peak in the GF(4096) parent. No complete DQI width,
Toffoli or score improvement is claimed.

An independent exhaustive meet-in-the-middle test considered only
products of rank-one data transvections guarded by affine functions of
the scalar, with invariant scalar coordinates and free unconditional
linear maps on the data. Each guard is normalized to inactive at
scalar 1; the resulting product has 147 possible step types. No
length-at-most-seven decomposition was found. The code does not claim
a bound for arbitrary ancilla-free circuits.

## Reproduction

```
python log_scaler.py --work /path/to/syed/controller_work --out log
c++ -O3 -std=c++20 search_scale.cpp -o search_scale
./search_scale TARGET_HEX
```

`TARGET_HEX` is the hexadecimal packing of the six multiplication matrices
for scalars 2 through 7, with nine bits each, least significant first.
For each matrix the three columns are packed in order as three-bit values,
also least significant first. Generate them with
`kickmix.GF2Field(3).mul(a, 1 << column)`. KMB files and verification
receipts are in `log/`.
