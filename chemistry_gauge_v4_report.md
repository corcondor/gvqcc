# Givens-tree sign gauge: exact factorization symmetry, unresolved loader cost

## What was actually checked

The pinned `submission_asterios_full.npz` has 1,220 vectors of dimension 76 and
75 ordered Givens angles per vector, encoded as `theta = pi * word / 128`.
Its first edge is `(0,1)`. Clearing bit 7 of angle column 0 changes **613 words**,
but only changes the overall sign of the corresponding reconstructed vectors.

The complete 1,220-row check and the unchanged official numerical evaluator gave:

| Quantity | Observed result |
|---|---:|
| Changed angle words | 613 / 91,500 |
| Maximum difference between new vector and predicted signed old vector | 5.5511e-16 |
| Maximum entrywise difference of `u u^T` | 6.1062e-16 |
| Maximum entrywise difference of weighted `X^(rho,c)` | 2.4980e-16 |
| Baseline and gauge-fixed `lambda_eff` | 46.90658950862355, identical |
| Gauge-fixed `error_1` | 19.99999799999905 mHa |
| Gauge-fixed `error_2` | 19.999998499405286 mHa |
| Official numerical conditions | Both pass |

These are rounding-level differences in vectors and errors, not a numerical
optimization. No matching loader, full circuit validation, or new Kaggle score
is claimed. All arrays except the derived `angle_words` table are unchanged.
The gauge table is recreated by the script; a duplicate full NPZ is unnecessary.

## Why it is exact

For the first rotation,

\[
G_{01}(\theta+\pi)e_0=-G_{01}(\theta)e_0.
\]

All subsequent rotations are linear and unchanged. Therefore, independently
for each address `a`, any Boolean choice `g(a)` permits

\[
w'_{a,0}=w_{a,0}\mathbin{\mathrm{XOR}}128g(a),\qquad
u'_a=(-1)^{g(a)}u_a.
\]

The two-body coefficients use `u u^T`; the one-body evaluator matches exact
eigenvectors using absolute overlaps and then also reconstructs outer products.
Both are invariant to this sign. Choosing `g(a) = bit7(w[a,0])` makes that one
output bit identically zero while preserving the represented chemistry.

This is a discrete sign symmetry of the vector parametrization. It is not a
generic SU(2^n) KAK decomposition or a quantum circuit with intermediate `Ry`
gates inserted. The relevant opportunity is to choose a cheaper representative
of an equivalent coefficient table.

The source evidence is in the pinned
`dfthcsos/scoreinfra/dfthc_math.py`: `reconstruct_u_vectors`, `reconstruct_x`,
`reconstruct_h1_thc`, and `evaluate_dfthc_angle_words`.

## A wider integer-angle symmetry family

At a tree edge the child amplitude is initially zero. For binary choices `s,k`,

\[
\theta' = (-1)^s\theta + k\pi \pmod{2\pi}
\]

remains exactly representable as
`w' = ((-1)**s * w + 128*k) % 256`. If the parent currently differs from the old
state by sign bit `z`, its new sign after the edge is `z XOR k`; the child's
sign is `z XOR k XOR s`. A sequence whose final signs are all the same preserves
every outer product. This recurrence follows directly from the sine and cosine
identities. Only the root-MSB member was evaluated numerically in this report.

These reflections are not generally affine XOR masks on the stored bits:
two's-complement negation includes carry/borrow structure. A larger symmetry
search must score the synthesized loader, not assume its transformations are free.

## Why the current loader cannot simply be reused

The optimized 4,033-Toffoli family carries five tags
`bit6(word) XOR bit7(word)` unchanged across its 15 batches. The original table
obeys this relation exactly. Clearing only the root-angle MSB destroys it.

The required address function is also **not address-affine**: the unique affine
interpolant determined by address 0 and all eleven single-bit addresses disagrees
on **615 of 1,220 addresses**. Thus the existing X/CX-only affine patch cannot
express this particular gauge fixing.

Even the simpler constant root-MSB toggle, which is affine and chemically valid,
is rejected by the already implemented wrapper: exact proof reports
`k=1/reverse, output mismatch, address 0, slot 0, bit 0`. The official reverse
traversal executes the same circuits in reversed batch order; this constraint
must be respected. It is unsafe to delete writes to `q18` merely because the
desired root MSB is zero.

## Useful next synthesis experiment

Use this symmetry as a free choice of the *target truth table*, then jointly
resynthesize batch 0 and the next tagged transition, including their reverse
contracts. Alternatively search the broader sign/reflection family subject to
preserving the five shared tags. Both could preserve chemistry exactly, so no
20 mHa approximation budget is consumed; neither has a demonstrated Toffoli
reduction here. A gain must be measured against the full original 4,033/pass
family and the 128-qubit per-loader limit.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python chemistry_gauge_v4_check.py
../kickmix_venv/bin/python chemistry_gauge_v4_check.py --loader-check
```

The first command uses the existing pinned source data/reference and SciPy;
the second uses the existing Kickmix environment and the v3 exact proof. Results
are recorded in `chemistry_gauge_v4_results.json`. The baseline SHA256 is
`809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`.
