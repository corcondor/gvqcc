# Public V8 W sparsity: audited coefficients and Lean 4.35.0 certificate

**Run:** [GitHub Actions #45310978106](https://github.com/corcondor/gvqcc/actions/runs/45310978106) — PASS; 136 seconds to kernel-build `SparseWCERT.lean`, 0 `sorry`/user `axiom`/`native_decide`.

**Provenance:** V8 `submission.npz` SHA256 `d4d39b2e2516ed7c51a936e863cf0567e558a0db8ded24e435f507d76bfb78d7`. Independently extracted C-order Float64 `W` bytes SHA256 `07133824492ef24ae9aae5e878b2c2af539b1c44ec3382f7a164a9e365af9d3a`. Support bit payload SHA256 `a67a006c8dd71ca47df915481eb0f8e830e745ccb58cd5af9ba7ce939a59d4e6`; full 1,143 row masks in compiled Lean artifact, each independently compared with source NPZ in a fresh local check.

**Formal assertions compiled by Lean 4.35.0:**
- Each of the 1,143 46-bit support masks has the specified population count (all nine 127-row chunks verified by kernel).
- Sum of nonzero entries = **41,437**; sum of exact zeros = **11,141** of 52,578.
- Every one of 1,143 (r,b) rows has at least one nonzero W entry; **74** rows have at most 23 nonzero channels, **141** rows have all 46 channels nonzero.
- Concrete source row (r,b)=(8,79) has seven nonzero channels: c=8,13,19,21,34,37,42.
- `sparse_dot_equal_full`: deleting zero-coefficient terms in any integer weighted sum preserves the expression for arbitrary values of the other factors. This is the algebraic ring identity used to prune the W-weighted contribution.

**Independent physical calculation (NOT a Lean theorem):**
- Using Givens-decoded public V8 U, computing `X[r,c,m] = sum_b W[r,b,c] P_m(U[r,b])` by NumPy dense and SciPy CSR sparse contractions produced **exactly the same numerical X** (maximum difference 0.0).
- The effective one-body coefficients `co[r,b] = sum_c W[r,b,c]*(H2_I[r,c]-sum_b' W[r,b',c])` were **nonzero for every (r,b)** (smallest absolute value 0.0649767974).
- The full 1,143-projector Gram matrix `G_{ij}=(U_i^T U_j)^2` was numerically positive definite (minimum computed eigenvalue ~7.876e-5). This is numerical evidence, **not a Lean-certified proof of nonsingularity**.

**Why this does not save 11,141 Toffolis:** the original ANGLE loader selects `U[r,b]` by its address, and has no independent c select pin. Every (r,b) still appears in at least one W coefficient and every effective one-body co[r,b] is nonzero. Algebraic zero-pruning in W removes 11,141 scalar contraction terms, **not** 11,141 CCX gates in the 3,357T loader. A c-conditioned ANGLE rewrite or joint W/U refit is a different architecture and must be evaluated by actual emitted KMB, full Q/T/HMR and official KickMix. No new scored KMB was constructed in this audit.

**Important proof boundary:** Lean checks the SHA-pinned bit support payload. SHA binding from the original V8 NPZ to that payload was validated by Python against the real original NPZ and rechecked against every compiled Lean mask. The Lean kernel does not parse NPZ/Float64 or formally certify the FeMoCo reference evaluator, and does not prove any optimization is impossible.
