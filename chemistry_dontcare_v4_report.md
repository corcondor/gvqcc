# Exact inactive-angle freedom: bounded loader-product pruning

## Result

The new physical freedom was tested against every existing extractable output-accumulation product in batches 1–14. **No single product can be deleted**, even if only the immediately produced batch is checked. Adding the necessary constraints from subsequent batches also gives zero candidates. The 188 products in each of batches 13 and 14 remain linearly independent after projecting out all permitted suffix don't-care bits, so deleting any nonempty subset of those existing products also fails the care constraints.

This is a bounded negative result for removing existing products. It does not rule out a different control/output basis, newly synthesized products, a different loader encoding, coordinated modifications across batches, or broader changes to the angle table. No optimality claim follows.

## Method and domain

The exact integer-quadrant tree propagation from `chemistry_gauge_v4_dontcare_check.py` identifies 1416 inactive angle entries, or 8496 independent low-six-bit don't-care positions. The underlying amplitude is structurally zero before the relevant Givens rotation. The mask was independently regenerated from the source integer words and tree; no floating-point tolerance was used.

The existing, separately verified `chemistry_joint_product_resynthesis.py` extraction provides both CCX control forms in a common entry frame and each target direction in a common exit frame. The new checker evaluates each pair of controls over all 1220 reachable addresses, propagates the full output direction through the circuit suffix, and checks every affected output bit. It verifies that the suffix introduces no nonlinear differential dependency or scratch difference. High bits 6/7 are retained as care bits for this experiment.

Deleting a low-bit product changes a transition, so its XOR persists in the same five word slots through subsequent batches. Since the original loaders depend on the preserved high-bit tags, a proposed deletion is accepted only if its complete difference lies inside the intersection of inactive masks for **every batch from k through 14**. Checking only batch k would be insufficient. Exact all-address forward/reverse and HMR-phase proof is mandatory in the implementation before any candidate is written.

Batch 0 was excluded: its internal nonlinear control updates are outside the existing extraction class. The investigation covers 2706 products, or 3,301,320 address/product cases.

## Coverage

| Batch | Products | Addresses affected per product | Immediate-batch hits | Whole-suffix hits |
|---|---:|---:|---:|---:|
| 1 | 212 | 260–387 | 0 | 0 |
| 2 | 212 | 252–369 | 0 | 0 |
| 3 | 212 | 251–351 | 0 | 0 |
| 4 | 189 | 249–357 | 0 | 0 |
| 5 | 189 | 252–345 | 0 | 0 |
| 6 | 187 | 248–347 | 0 | 0 |
| 7 | 189 | 258–344 | 0 | 0 |
| 8 | 187 | 270–347 | 0 | 0 |
| 9 | 189 | 261–354 | 0 | 0 |
| 10 | 187 | 258–350 | 0 | 0 |
| 11 | 189 | 240–354 | 0 | 0 |
| 12 | 188 | 266–350 | 0 | 0 |
| 13 | 188 | 256–343 | 0 | 0 |
| 14 | 188 | 252–360 | 0 | 0 |

Of the 2706 products, 2625 also affect high output bits. Every product has nonzero support, between 240 and 387 addresses. Even the least disruptive product violates 1526 cared address/output-bit positions in its immediate batch; this is a count of bit positions, not unique addresses.

For batches 1–12, the intersection of inactive-address sets over all subsequent batches is empty for every slot. Batch 13 permits only `[0,6,0,2,2]` addresses in the five slots, respectively; batch 14 permits `[22,24,13,41,36]`.

## Collective-deletion extension

For batches 13 and 14, exact GF(2) elimination was performed on product-contribution columns, with a separate coordinate for every address/output bit. Columns were examined before and after projecting away the suffix don't-care coordinates.

| Batch | Products | Full output rank | Care-projected rank | New nullity |
|---|---:|---:|---:|---:|
| 13 | 188 | 188 | 188 | 0 |
| 14 | 188 | 188 | 188 | 0 |

A nonzero kernel vector would have identified a subset whose combined deletion changes only allowed coordinates. There is no such vector in either examined batch. This does not assess replacements by new bilinear products or coordinated changes at different batch positions.

## Files and verification scope

- `chemistry_dontcare_v4_prune.py` and `chemistry_dontcare_v4_results.json`: single-product screening and guarded candidate emitter.
- `chemistry_dontcare_v4_rank.py` and `chemistry_dontcare_v4_rank_results.json`: exact projected-rank calculation.
- Source factorization SHA-256: `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`.

Single-product screening consumed 2.411 CPU seconds; the rank extension consumed 0.333 CPU seconds. Peak screening RSS was 51.69 MiB. No original file was changed. No candidate NPZ/KMB, full-shot validation, external push, or submission was produced because no deletion passed the necessary output checks. Consequently there is no new measured gate reduction or score gain from this specific experiment.
