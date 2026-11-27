# 316k repair: reproducible status, 2026-11-28

**The 316k decoder is not repaired. No competition submission was made.**
The previous 1244/1244 result executes different native circuits chosen outside
the quantum circuit. It is not evidence that one repaired decoder has zero
errors. The existing Lean algebra theorems do not assert that either.

## Native regression on one circuit

`validate_repair.py` executes one fixed circuit on every selected input. There
is no syndrome-dependent external chart-selection callback. Prefix/suffix
arguments, when supplied, are fixed for every input. The checker restores and
checks the original syndrome, mask, phase and ancillas. This is not an unchanged
official verifier invocation, and it does not establish whole-domain correctness.

| Circuit / panel | Shots | Value failures | Official disjoint phase failures | Raw phase mismatches |
|---|---:|---:|---:|---:|
| Exact original 316k parent, all 622 diagnostic inputs | 1244 | 904 | 5 | 474 |
| Fixed +1 rotation, inverse-transformed 45 old counterexamples | 90 | 90 | 0 | 43 |
| Separate existing V127 reference, original panel | 1244 | 0 | 0 | 0 |
| Separate existing V127 reference, inverse panel | 90 | 0 | 0 | 0 |

The reference is a different circuit with roughly 410974 mean paid gates. Its
passing tests are not a 316k repair. All four receipts contain source hashes.
These are deliberately adversarial diagnostics, not estimates of official
failure probability. Value failures take precedence in the official disjoint
phase counter; raw phase mismatches include value-failing shots.

Example, using the previously published affine-chart archive's fixtures and
the separately supplied exact parent KMB:

```sh
python validate_repair.py /path/to/donor33170.kmb \
  --cases /path/to/hybrid_cases.npz \
  --verifier /path/to/verify_submission_dqi.py \
  --panel high-inverse --rotation-receipt /path/to/rotation_receipt.json \
  --prefix /path/to/rotation_pre.kmb --suffix /path/to/rotation_post.kmb \
  --out rotation_rejected.json
```

The parent hash must be
`4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52`.
The command above correctly returns exit status 1. It rejects fixed rotation
as a repair. The proposed rotation is a bijective change of coordinates, so
inverse-transformed old failures cannot be removed by that fixed conjugation.

## Concrete parser proof

`ParserStability.lean` defines a bounded first-nonzero scan and a precision
check, and proves 9 theorems about their stability under nonzero-head inversion
and changes to the suffix. Lean 4.35.0 strict compilation completed with exit 0,
no warnings, and only `propext`, `Classical.choice`, `Quot.sound` dependencies;
see `parser_stability_lean.log`. The existing workflow now checks this file.

This discharges the first-nonzero/remaining-precision part of the abstract
stable-selector condition. It does not prove the native gate tape implements
the reciprocal, the entire boundary-counter parser, or the complete decoder.

## Concrete replacement components

`emit_coherent_codec.py` streams a forward/reverse coherent Laurent codec,
including every possible branch and computed quantum guards. The 8-word
instance passed 304 native checks, but costs 223659 paid gates. The full
70-word instance was not emitted. On the actual 70-word dyadic reciprocal,
the current generic controlled lift costs 1895736 paid gates for the first
reciprocal alone, excluding its guards. See `coherent_codec70_cost_bound.json`.
This is a bound for this emitted implementation, not a general lower bound.

`continuant_phase.py` connects quotient words to sparse magnitudes and phases
without reconstructing all coefficient polynomials. The classical 70-word
check passed 737 legal inputs, 12662 magnitude/root checks, 2948 additional
position checks and 667 supplied-mask phase checks against an independent
Hankel solver. Three native controlled quotient transitions passed 768 shots
on arbitrary inputs. These transitions are components, not a full oracle.
Both scripts require the separately pinned infinity-CF source and upstream
kit via their explicit `--source` and `--kit` options; no kit is re-licensed here.

The remaining task is a competitive complete 70-word coherent decoder and
phase oracle, including exact branch computation and uncomputation. There is
no fully integrated repaired KMB, whole-circuit Lean refinement, new official
score, or competition submission in this change.
