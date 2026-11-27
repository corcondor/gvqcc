# 316k DQI exact syndrome guard — research only

**This is not a repaired DQI KMB, not a new paid-gate score, and not a submission.**

- Pinned donor: 900Q / 62,086,097 instructions / 311,868 CCX / 6,716 CCZ / SHA-256 `2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60`.
- The PR #231 rank-0/1 padding experiment starts instead from `4b572141...` / 69,782,188 instructions. **Never transfer verification receipts across these donors.**
- Reuses existing `InvariantPad.moments_injective`; the new Lean theorem handles DQI's moments at exponents 1..70 (nonzero roots mandatory). It proves support uniqueness for two valid weight<=35 inputs, **not** correct restoration by a faulty KMB.
- A small Hankel determinant alone is unsafe as a rank test: roots 1,2,4 with magnitudes 1,1/2,1/4 produce a rank-3 syndrome whose first 2x2 minor vanishes. All 70 moments and roots/magnitudes must be checked.
- `syndrome_guard.py` is an exact, fail-closed **classical** GF(4096) rank<=2 witness. It does not infer original input correctness from the possibly corrupted output. Native oracle checking must additionally restore the original 70-word syndrome and input mask, zero dirty ancillas, and repay phase for every HMR branch.
- The finite-difference Boolean law includes its mandatory mixed term `delta(a)*delta(b)`.

**Local validation:** `python test_syndrome_guard.py`. The archived V114 panel was independently audited offline: 256 actual 62,086,097-op native output vectors, 216 incorrect; only two already correct zero-syndrome vectors are accepted by this conservative witness, zero corrupted outputs were accepted. The 216 output faults are NOT repaired.

**Lean 4.35.0:** CI compiles the existing `InvariantPad.lean` to an OLean before checking `SparseSyndromeGuard.lean`, with warnings as errors and a forbidden-`sorryAx` check. The Lean proof is local mathematics, not KickMix whole-tape refinement. The Python CI reference checker does not execute KickMix. **A future KMB must pass full KickMix and official verifier before approval.**

Next steps: diagnose first incorrect internal update, implement coherent rank-selecting repair that is correct for all weights<=35, prove phase including exact SSA measurement epochs, and only then optimize Q² × expected paid × repetition-factor on the same fixed native distribution. No main-branch merge or Kaggle upload is authorized by this research-only change.
