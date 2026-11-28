# Exact depth-two merge, including reversible frame preparation

The dense degree profile of the #261 raw archive is 1,095/1,249. We tested the
17→16→15 merge at the top of that profile, over GF(4096), with monic Laurent
frames and both numerator sectors on the physical 865Q #261 map.

Let (T_a) be the unit upper-triangular Toeplitz action of normalized Laurent
coefficients (a) on the 17 packed words (p=(p_0,p_1,W)).
Full triangles compose as (T_fT_g=T_{fg}). The actual inner merge does not
touch (p_0), so the outer merge fixes the difference, namely the first-row
word (g_1p_1+g_2W_0+\dots+g_{16}W_{14}). The exact fused map is (T_{fg})
with that word XORed into slot zero. This derivation uses the same recurrence
as the earlier Euclidean adapter; it does not treat intermediate polynomial
truncation as multiplicative. In the KMB, the correction precedes the full
triangle, which fixes that coordinate vector. The inverse reverses these
two steps and all recursive cross-block shears.

Two sectors share each interpolated coefficient basis change. The prior
single-sector 8×8 and 7×10 receipts reproduced at identical KMB hashes.

| Variant, both sectors, one direction | CCX | Paid | Instructions |
|---|---:|---:|---:|
| Separate merges from live (f,g) | 8,652 | 8,652 | 309,420 |
| Fused from **precomputed** (fg,g) | 5,880 | 5,880 | 181,008 |
| Fused from **the same live inputs** (f,g), compute and restore (f) | 9,996 | 9,996 | 371,084 |
| Fused without boundary correction (incorrect) | 4,536 | 4,536 | 164,688 |

All exact forward/inverse serialized KMBs passed 1,024 KickMix lanes in each
direction. All 865 wires, phases and dynamic paid counts were checked. The
negative control failed on 1,024/1,024 lanes, with each discrepancy localized
to the boundary word, as predicted. No extra working qubits or standalone
T gates were emitted. Two local cancellation and inverse lemmas passed
Lean 4.35.0 with warnings as errors; these do not prove the finite-field
frame synthesis or the full DQI circuit.

The equal-input comparison is decisive: generating and undoing (fg)
costs 4,116 paid per pass and exceeds the 2,772 merge saving. Do not adopt
this lowering as-is. Using a direct B/r frame from earlier extraction, or a
frame that survives both sweeps while still allowing the existing phase tape
to access its inputs, could change the trade, but is not implemented.
Even if coherent setup were free, applying disjoint pairs down the dense
profile would take the previous 128,352 CCX adapter model only to 109,704
(42 per scalar slot, including four sector/direction traversals). The merged
part alone still costs 47,376 in that model. No route to 26,384 is established
by this two-step change. No raw-syndrome tape, official score or submission.

Reproduce with the CRT modules and dependencies listed in the sibling
[README](README.md), then:
```sh
python dense_pair.py /tmp/dense_pair
lean -DwarningAsError=true DensePair.lean
```
