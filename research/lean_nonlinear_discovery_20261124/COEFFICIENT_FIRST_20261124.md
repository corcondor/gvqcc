# Coefficient-first GVQCC k8 audit (2026-11-24)

**Actual parent:** public maoxin123 V8 `angle_k_8.kmb`, SHA256 `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`, Q128, **211 CCX** (82 cache, 129 output).

The previous optimizer searched deletions of the existing 129 terms. The new task is **not** another fixed-gate search. Extract its **whole quadratic coefficient tensor**, and synthesize a different tensor decomposition.

## Exact recovered structure

- 128 cut-state bits, but nonlinear controls use 98 independent directions: 11 address, **5 word bit-6 controls**, all 82 cached bits. The other **30 low word bits** do not occur in any nonlinear-control affine form (but may matter to linear output; they are **not** 30 free qubits).
- 35 output quadratic polynomials have **rank 23**; **10 are affine-only** (positions 0,6,7,13,14,20,21,27,28,34).
- Two independent output-quadratic relations: `Q1 ^ Q15 ^ Q29 = 0` and `Q8 ^ Q15 ^ Q22 = 0` (indices 0-based; full output equalities require affine correction).
- Exact target `T ∈ Λ²(F₂^98) ⊗ F₂^23`, initial rank-one decomposition with 129 terms.
- The original **129 vector-valued tensor terms are linearly independent**. There is no zero-cost deletion of any old factor by XOR-only feedback.
- Among 129 factor-pairs, **0 of 8,256 projective 2-plane pairs share a factor** (even after `(a,b)∼(a,a⊕b)`), proving a standard shared-factor two-term flip cannot begin at this initial decomposition.
- A nonmonotone `1→2 split` and two-term flip produced an exact **130-term different tensor decomposition**, introducing **four input factor forms** outside the old support. Exact polynomial reconstruction PASS for all 35 quadratic outputs; not an emitted KMB.
- Data-level `W` coefficients: `W.shape=(9,127,46)` contains **11,141 / 52,578 exactly-zero entries** (21.19%), but 0 entirely-zero (rank,atom) rows. Thus W sparsity alone does **not** validate deleting a whole ANGLE vector.

## Concrete next search contract

```
seek T = Σ_{j=1}^{r} (a_j ∧ b_j) ⊗ c_j,
  a_j,b_j ∈ F₂^98, c_j ∈ F₂^23,
  r ≤ 128;
permit temporary r > 129 and changes to all factors.
```

Use exact coefficient reconstruction and negative controls before resource lowering. Reject the false inference `rank(output coefficient matrix)=23 ⇒ 23 CCX`. After finding a genuinely shorter tensor factorization, implement an actual reversible KMB and check width ≤128, reachability, clean scratch, HMR phase, reverse traversal, then unchanged KickMix verifier.

**Evidence and runnable package** were generated in the associated conversation: `GVQCC_CoefficientFirst_98x23_20261124.zip` (input parent KMB/NPZ, compressed tensor JSON, exact candidate checker, 129→130 structural move and positive/negative controls). The original KMB SHA is pinned above. GitHub does not yet host the archive bytes. This note is *not* a score improvement or a Lean proof of a new KMB.
