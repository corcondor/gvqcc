# GVQCC public V8 tensor: Lean 4.35 formal verification status

Parent: public V8 k8 KMB SHA256 `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`. The 129 output-directed terms were recovered from the source into `V8TensorCertificate.lean`. The original circuit has 82 scratch CCX and 129 output CCX, totaling 211.

## What is proved by the kernel (no sorry / additional axioms)

1. `original_count`: exactly 129 rank-one summands.
2. `changed_count`: a concrete split+flip transform produces 130 summands.
3. `original129_eq_changed130`: **for every one of 2^98 abstract cut-input states**, and every 35 output bit, the 129- and 130-term Boolean outputs agree. All 129 original factor coefficients are embedded in the Lean source; the rewired factors are constructed from the actual terms 1 and 2.
4. `naive128_is_not_equivalent`: a specific invalid 128-term candidate (delete original term 1) differs on cut input with bit 3 set and output bit 2. This is an out-of-contract counterexample to unrestricted equivalence, not a counterexample on legitimate reachable states.

This is a certified *nonmonotone* move in the original public coefficient tensor, **not** a 210T KMB. It proves an exact Boolean identity rather than a tensor-rank lower bound or the cost of realizing this move.

## Important trust boundary

- The KMB byte-level parser and the extraction from raw gates into 98-bit factor masks are currently verified independently with Python; that extraction is **not formalized in Lean**. The Lean theorem is conditional on those embedded coefficients being the correct source-to-tensor extraction.
- The actual 130-term candidate uses normalized XOR masks. The Lean certificate carries XORs as explicit `LinExpr.plus` nodes; numerical normalization into masks remains externally checked.
- Resource width, ancilla recycling, measurement-conditioned phases, output affine correction, forward/reverse bank order, and the full official KickMix simulator have **not** been verified for a new KMB.
- No candidate with fewer than 129 terms (or fewer than 211 CCX overall) has been certified. No Kaggle score improvement is claimed.

## Required architecture to obtain a score gain

The synthesis/search stage needs to propose a *different global tensor factorization* with a strictly lower **actual** cost. Every accepted new factorization should emit a Lean theorem `∀ x j, evalTerms original129 x j = evalTerms proposal x j`, and a proof of the exact number of summands. Then emit and independently check a real reversible KMB with the ≤128Q bound and phase/HMR constraints. Neither the previous 5.71e8 fixed-gate combination scan nor another randomized seed sweep in the same restricted architecture satisfies this goal.

CI action builds `GVQCCRelational` and `V8TensorCertificate` using pinned Lean 4.35.0.
