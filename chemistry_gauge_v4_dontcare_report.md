# Exact zero-parent angles give chemistry don't-cares

## Result of the bounded check

The pinned 8-bit Givens table contains **1,416 angle entries whose parent
amplitude is mathematically zero immediately before that rotation**. The tree
introduces a fresh, zero child at every edge, so rotating these two zero
amplitudes leaves the reconstructed vector unchanged for any angle value.

Keeping the two high bits unchanged, these entries provide **8,496 low-bit
positions** that can be selected during loader synthesis without altering the
represented chemistry. This is a freedom in choosing the target table; it is
not permission for a circuit to disagree with its submitted angle table.

One concrete canonicalization set bits0..5 to zero in every inactive entry:

| Item | Actual result |
|---|---:|
| Inactive angle entries | 1,416 |
| Changed angle words | 1,349 |
| Changed low bits | 3,923 |
| Bit6/bit7 and shared loader tags | All unchanged |
| Maximum entrywise vector change | 1.7958e-16 |
| Maximum entrywise outer-product change | 1.7818e-16 |
| `lambda_eff` before and after | 46.90658950862355, identical |
| Canonical `error_1` | 19.999997999998877 mHa |
| Canonical `error_2` | 19.99999849940529 mHa |
| Official numerical conditions | Pass |

The official evaluator was run once on this single canonicalization. Its
baseline comparison comes from the previously evaluated, SHA-matched same
factorization. Numerical differences are floating-point rounding, not a
physical error-budget expenditure or objective improvement.

## Exact detection, with no floating tolerance

Angles are `theta = pi*word/128`. The only zero tests are integer identities:

- `word % 128 == 0` means `sin(theta) == 0` mathematically.
- `word % 128 == 64` means `cos(theta) == 0` mathematically.

Initialize only coordinate0 as active. At an ordered tree edge `(p,c)`, record
the angle as inactive if `p` is inactive. Then set

```python
active_parent_after = active_parent_before and (word % 128 != 64)
active_child_after = active_parent_before and (word % 128 != 0)
```

Every child is new, so its incoming amplitude is exactly zero and each output
is a product of the old parent with one sine/cosine. There are no cancellation
heuristics in this rule. Changing only inactive angles cannot reactivate those
coordinates; the script verifies that the complete inactive mask is unchanged
after simultaneous canonicalization.

The counts by batches0..14 are:
`[0, 5, 6, 86, 40, 137, 61, 137, 153, 203, 90, 144, 117, 101, 136]`.

## How this can help synthesis

An XAG/ANF synthesizer may choose these target low bits to reduce shared AND
terms while preserving every active angle and the two high bits. Setting all
such bits to zero was only a verification example, not a claim of an optimal
completion. Each chosen completion must be emitted into both the NPZ table and
matching forward/reverse loader circuits, and then pass their exact contracts.

The current 4,033-Toffoli loaders have not been resynthesized for this table.
Preserving their shared tags is necessary for some existing transformations but
does not make arbitrary low-bit truth-table changes implementable for free.
There is no measured Toffoli/qubit reduction, full circuit validation, or new
Kaggle submission from this check.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python chemistry_gauge_v4_dontcare_check.py
```

This uses the pinned scientific environment and the existing
`chemistry_gauge_v4_results.json` baseline, whose source SHA256 is checked.
The output is `chemistry_gauge_v4_dontcare_results.json`. No full NPZ duplication
is needed: the script deterministically regenerates the canonical table.
