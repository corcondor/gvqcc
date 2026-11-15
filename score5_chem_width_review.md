# Independent review: child-norm qubit borrowing

**No concrete defect was found in the reviewed component.** This is a
read-only review of the implementation, its algebra and storage contracts,
and the existing component receipt. It is not a rerun of the native tests or
a whole-decoder official verification. `score5_chem_width_review.json` binds
the reviewed source hashes, all six KMB artifact hashes, receipt, and cost
reference.

## Why borrowing is exact

Let `A` be the still-live 12-bit parent norm, represented as a quadratic
extension of GF(64), and let `n=N(A)` be its 6-bit child norm. For tower
coordinates `(L,R)`,

`n = L² + L R + delta R²`.

The new code maps `A` to that tower basis, XORs either the selected polynomial
coordinate of `n` or all six coordinates into `child_norm`, and maps `A` back.
The selected child coordinates therefore become exactly zero, with no
measurement or additional phase. Squaring terms are linear. One selected
product coordinate uses six CCX; the full GF(64) product uses the existing
15-term multiplication tensor. Performing the toggle twice costs 12 or 30
CCX per inverse call.

The clean coordinates are included in the temporary multiplication output,
whose full length remains twelve. Each consuming product is swapped into the
source half, and HMR resets the previous source value in the temporary array.
After both such loops every borrowed coordinate is again zero. Only the
separately allocated temporary array is freed; caller-owned bank bits are
never handed to the allocator as free storage.

The HMR phase of each previous source half is paid with the updated half and
the surviving parent norm. Their product reconstructs the measured old half.
The zero case also holds: the irreducible extension norm vanishes only for
zero source, and `inv0(0)=0`. None of these corrections reads `child_norm`
while it is borrowed.

The second norm toggle restores the exact child norm **before** the parent
norm HMR. If the inverse parent has tower coordinates `(X,Y)`, the measured
original parent is `((X+Y)n, Yn)`, precisely the witness used by the existing
phase correction. The later child HMR mask remains a mask of the child's
tower coordinates. The return call pays the saved mask before modifying its
reciprocal witness. These coordinate conventions are preserved by the change.

## Existing evidence checked

The component receipt reports an exhaustive 4096-pair check of the one-bit
norm identity and, for each variant, native tests of 512 GF24 inputs under
each of two fixed seeds. The source, initially arbitrary flag, cleaned bank,
scratch, and phase checks all pass. The fixture inserts both a classical
linear phase probe and a cubic CCZ phase on the intermediate inverse, so it
does not merely test an inverse followed immediately by its inverse.

| Variant | Pair Q | Pair static T | Whole chart template Q | Chart static T |
|---|---:|---:|---:|---:|
| Original | 73 | 389 | 889 | 1260 |
| Borrow one child bit | 72 | 413 | 888 | 1332 |
| Borrow six child bits | 67 | 449 | 883 | 1440 |

The pair fixture includes its extra CCZ probe. Relative increments are 24/60
for a matched inverse pair and 72/180 for the three-pair chart. The receipt's
source hashes match the current files; the saved KMB hashes also match.

## Global width and score obligations

The actual DQI score is **R × Q² × mean_T**. With the full verified score5
reference Q=889, mean_T=382068.47728515626 and unchanged R, the conditional
figures are:

| Actual global width, if achieved | Added T from this component | Same-R score ratio | Total added-T break-even allowance |
|---|---:|---:|---:|
| 888 | 72 | 0.9979395707014188 | 860.9991124601 |
| 883 | 180 | 0.9870120202747122 | 5209.964550604 |

These ratios are projections, not measured full-candidate scores. The whole
circuit must eliminate every other peak, compact or rename the physical
quantum wires consistently, retain the public ABI, and restore every borrowed
gap to zero before its next owner starts. Remaining peak repairs may spend
some of the indicated total overhead budget. A local template whose maximum
wire number falls is insufficient by itself.

The enclosing chart's finite-output contract is unchanged. The matched return
still requires the same physical source to hold `inv0(prefix-entry)`; Python
record checks do not prove that quantum value condition. A final comparison
should use common inputs to establish that the full decoder's values, phases,
and failure events are unchanged. The official full run is then a separate
gate for the selected actual candidate. Its default cohort may change with
the file hash, so the table above explicitly assumes the same input cohort
and repetition factor.
