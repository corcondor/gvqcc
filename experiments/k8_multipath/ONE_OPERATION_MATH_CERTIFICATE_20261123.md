# One-operation mathematical certificate — ANGLE k8 public 211T (2026-11-23)

**Verification goal:** Prove one *actual* KMB edit by exact Boolean algebra over all 46 independent input bits, not by random inputs, proxy rank, or just 1219 table rows. **Result: exact equivalence, but NO Toffoli reduction (211 -> 211).**

Baseline source: [Kaggle 33.17023 V8](https://www.kaggle.com/code/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders), author's 15 loaders maoxin123, k8 SHA256 `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`.

## Chosen single operation

Original zero-based op 389:
```text
CCX q115 q48 q123
```

Replacement:
```text
CX q56 q115
CCX q115 q48 q123
CX q56 q115
CX q71 q123
```

**Precondition derived from the real original 389-instruction prefix:**

`q71 = q48 AND q56`.

We represented *all 128 wires* exactly as algebraic-normal-form polynomials of the 46 independent bits (address11 + arbitrary incoming word35; initial workspace 0), in the Boolean quotient ring `GF(2)[x0,...,x45]/(xi^2-xi)`. Across all actual prefix gates X, CX, CCX, the ANF of `q71 XOR(q48 AND q56)` has **zero terms**: exact identity for all `2^46` input assignments.

Let `a=q48, b=q115, c=q56, t=q123, u=q71=ac`. The replacement maps `t -> t XOR a(b XOR c) XOR u = t XOR ab` and restores `b`. All 128 wire polynomials match immediately after the replacement. No phase or measurement gates were introduced and the suffix is byte-identical in its gate list. Therefore the full forward quantum channel is exactly unchanged under the zero-workspace contract, for arbitrary input word values (not just the 1219 known words).

Crosschecks: all 16 local truth-table valuations with u=ac passed; all 16 deliberately violated-u cases detected; independent bitset simulator passed 2048 addresses x 4 word register configurations with all 128 wires equal; 1219 supplied table addresses in both 7->8 and 8->7 passed output, scratch=0 and symbolic HMR-phase tests. SHA after edit: `ddf57e42c11d8922e9361e292d08bb20de7dcd6b6fb1d6f191cb4a8e5acbbb48`. Q remains 128, CX 28935->28938, T remains 211. Official competition score was not run.

## A concrete failure of overgeneralizing row tests

Previous alternative op 186 relied on `q86=q4*q52`. Its exact ANF discrepancy is

`q86 XOR(q4 AND q52) = x4*x5*x8*x10*(1 XOR x6)*(1 XOR x7)`.

This is nonzero on 32 of all 2048 addresses; first counterexample `a=1328`. It is zero on the previously tested 1219 table addresses. So a legal-row PASS **does not prove universal operator equivalence**. The finite-domain claim remains valid but must be labeled explicitly.

## Reproducible code and sources

The conversation artifact `GVQCC_K8_ONE_OPERATION_MATH_CERTIFICATE_20261123.zip` holds the original KMB, changed KMB, `prove_single_ccx.py`, `native_kmb.py`, `independent_bitset_check.py`, `verify_bidirectional.py`, `check_bidirectional.py`, `proof_result.json`, `README_JA.md`, hash manifest, and one-command `RUN_ONCE.sh`. A fresh extraction and `bash RUN_ONCE.sh` reproduced both SHA values and PASS.

**Engineering rule for A/B/C:** Before claiming a new pattern is correct, specify the exact state invariant, prove the one-gate identity in the relevant Boolean/phase semantics, compare the complete wire-state after the patch, then independently verify the actual KMB. Exact equivalence is distinct from measured cost improvement.