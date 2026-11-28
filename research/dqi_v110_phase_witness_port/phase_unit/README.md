# Low-storage Euclidean numerator action

The missing #246 adapter operation is to overwrite each reduced numerator sector
(P) by (U=A^{-1}Pmod B) without storing a 17-word inverse or a second
numerator. `unit_profile.py` is a forward/reverse word oracle for that operation.
It is not a native implementation of the adapter.

Write (B=Aq+r, P=Ap+s). Recursively overwrite the remainder by
(Z=r^{-1}smod A), and merge using (U=p+lfloor BZ/A
floor). The result
satisfies (AU=P+BZ) in characteristic two. Store (p) in the first (n-m)
words and (Z) in the last (m), where (n=deg B), (m=deg A).
The first (n) Laurent coefficients of (B/A) give triangular updates on
this same target, with nonzero diagonal, so the merge can be undone.
Control storage, coefficient generation and erasure are not proven by this
word model. `EuclideanUnit.lean` checks the core ring identity and local inverse
steps with Lean 4.35.0, not the full circuit.

## Native input profile falsifies the short-descent assumption

Regenerated the #261 pinned raw prefix and key closing (102,066 and 220,343
static paid, 889Q and 890Q). All 1,249 archived inputs passed reference moment,
phase-mask (where present), and native key round-trip checks. Then both numerator
sectors (2,498) were checked with the new oracle, against independent modular
inverse multiplication as well as its own reverse map.

A full degree-17-through-0 descent occurred in **1,095/1,249** cases (87.67%),
including the exact old 423-bit w33 witness. It also occurred in **165/169**
inverse-Frobenius controls. This is a fixture histogram, not an estimate of the
official distribution. The most severe gap (16→3) occurred in 39 cases.
The 16-bit degree occupancy observation does not price coherent branching.

## Native cross-block test, no extra storage

Reused the #261 rank-42 GF(4096) multiplier and #246 spectral transposition.
Interpolate the polynomial of length (r+s-1) against the coefficient
functional, giving one scalar product per point. Dirty outputs are temporary
basis frames, and inputs are restored after each product. Reverse the input
ordering to realize the Toeplitz cross block. Lane tests used arbitrary values
on all 865 seam lines. All four serialized KMBs passed 1,024 lanes in each
direction: values, spectators and phase checked.

| Coupon | Scalar CCX / paid | Blocked CCX / paid | Scalar → blocked instructions |
|---|---:|---:|---:|
| 8×8 split inside the degree-16 triangular merge | 2,688 | 630 | 32,640 → 58,018 |
| 7×10 example of a multi-degree transition | 2,940 | 672 | 35,700 → 65,047 |

The second coupon prices that rectangular size, not a separate full native
path. There are no standalone T gates in these coupons. The paid reduction
does not imply lower instruction count. Coefficients are live inputs to the
coupons, not generated here. Reusing the word addresses does not establish
that those exact slots can hold the coefficients during a full traversal.

For two sectors forward/reverse at 42 paid per scalar product slot, the
arithmetical dense-path estimate is **185,640→128,352** with blocked merges,
excluding coherent coefficient and control generation, storage, cleanup,
and actual cost of variable in-place scales. Even the 16→3 observed path's
estimate is **30,912**, above the nominal 26,384 static allowance. These are
model counts for a schedule, not mathematical lower bounds. Improving
individual mergers is insufficient. The expensive work remaining in this
model includes repeated quotient/remainder splitting and scaling; optimize
across consecutive Euclidean steps, not just within one merge. No replacement
full DQI, official score or submission is produced here.

## Reproduction

Copy the #261 sources at `bf87158c58b5f183f08798d6d449e42c10177019`,
including `research/dqi316k_joint_crt`, to `PYTHONPATH` with KickMix 1.0.0 and
NumPy 2.2.6. Use `phase261/audit_raw_prefix.py` and the pinned raw fixture archive
for `raw_words.jsonl`. Then:

```sh
python unit_profile.py raw_words.jsonl --out profile_receipt.json
python toeplitz_native.py /tmp/unit_kmb 8x8 7x10
lean -DwarningAsError=true EuclideanUnit.lean
```
