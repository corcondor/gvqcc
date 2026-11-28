# V10: invariant-control vector transvections + exact affine words

Research only. Do not submit or merge into main. Base PR51 (8ae3491039b6e0917a0599d8aa82256b594d290b); independently apply compiler to PR50 and PR51 actual cost/width archives. No arithmetic addition of overlapping improvements.

## Actual circuit results
| branch | parent native instructions / static paid / expected paid | new native instructions / static paid / expected paid | source coverage |
|---|---|---|---|
| PR50 cost | 42624 / 1865 / 1694.3125 | 42631 / 1856 / 1685.3125 | 55485/60766 |
| PR50 wide | 47095 / 1913 / 1726.3125 | 47114 / 1892 / 1705.3125 | 55829/60766 |
| PR51 cost, vector only | 42144 / 1863 / 1693.3125 | 42149 / 1852 / 1682.3125 | 55485/60766 |
| PR51 wide, vector only | 43161 / 1899 / 1718.3125 | 43176 / 1882 / 1701.3125 | 55829/60766 |
| final cost, affine-word cleanup | 42149 / 1852 / 1682.3125 | 41816 / 1852 / 1682.3125 | 55485/60766 |
| final wide, affine-word cleanup | 43176 / 1882 / 1701.3125 | 42767 / 1882 / 1701.3125 | 55829/60766 |

Final native SHA256:
cost 6cb9812fc645caf2969e48713aed83a264d4e67ed42481b4ce109efbde2e5afe
wide 72f37d9897c3d036df04d2a155db6f4e715cde74418c458f6d9a6c1421e51360

## New synthesis structure
Conjugate each CCX through the accumulated affine scaffold into a common input frame: x -> x xor v A(x) B(x), with v a vector and A,B affine forms. For the selected invariant layer every control form annihilates every update direction. Thus the whole layer is a vector-valued quadratic polynomial with a shared output space. Enumerate the nonzero quadratic forms in that output span, split alternating forms by symplectic elimination, choose a minimum-weight independent basis (weights = half alternating rank), and lift controls back to actual wires. Restore the affine residual, synthesize native X/CX/SWAP/CCX, and independently check the full Boolean ANF for every wire. No claim of global tensor-rank optimality. The PR50 search tested up to 16 CCX and 240 instructions (2667 cost / 2861 wide windows); PR51 search tested 2668 / 2857 windows, 222 / 242 invariant layers, 85 / 105 output-rank gaps, 11 / 20 valid candidates, selecting 9 / 14 disjoint intervals. On PR51 all selected gates are unconditional and use q0..35.

A second exact pass enumerates shortest words over native X/CX/SWAP on at most 3 affine or 4 linear wires (SWAP costs one native instruction, not three CNOTs), then weighted interval scheduling. 10927 / 12734 windows, 617 / 730 positive, 275 / 290 accepted, 333 / 409 native commands eliminated. No paid increase. Distinct from Gaussian-order heuristic; not a global circuit shortest word guarantee.

## Exact validation
Every replacement is universal ANF equal, native roundtrip and chart widths checked. Fresh independent paired BDD, including classical state, relative phase, rotations, 3133452 legal inputs and independent HMR histories:
- PR50 cost -> vector 42569 comparisons PASS (1174 HMR, 1694.3125 -> 1685.3125).
- PR51 cost -> vector 42081 PASS (1174, 1693.3125 -> 1682.3125).
- PR51 wide -> vector 43069 PASS (1186, 1718.3125 -> 1701.3125).
- PR51 cost vector -> final 41294 PASS (1174, unchanged expected paid).
- PR51 wide vector -> final 42244 PASS (1186, unchanged expected paid).
PR50 wide has universal ANF proof and exact native splice, not a fresh whole-circuit BDD result.
VectorRankV10.lean contains 23 concrete unconditional gate-list theorems and 23 width/cost theorems on 37-bit state; CI configured. It does not certify the full oracle or the 565 affine-word edits in Lean.

## Width-negative experiment and next architecture
91 residual wide gaps: 88 have one HMR, remaining three have 2, 7, 9 HMR. New persistent-carrier cluster screen spanning 2..8 gaps: 609 clusters; 374 eligible idle-carrier clusters; 4288 endpoint decoder queries; 2551360 product probes. Two-product affine quotient decoding found zero sampled candidates; no exact candidate and no added coverage. Do not repeat same architecture simply increasing trials. Need an instrument-preserving, moving nonlinear multi-output representation across measurement events, not another idle payload loan. Full circuit remains peak 37Q.

## Conditional score
Same PR43/50 model only: S=S0*(C0/[Q(E+K)])^(1/3), S0=33.1703164053, C0=60927.5479450, K=240.3779850. Final cost E=1682.3125: Q37 predicts 31.50047823; hypothetical full Q36 predicts 31.78948959. Final wide E=1701.3125: Q37 31.39739418; hypothetical Q36 31.68545976. Need E<1452.05390236 at full 36Q, another >230.25859764 expected-paid saving for cost. Not official score or submission.

## Primary literature / research directions
- Boyar and Find, Multiplicative complexity of vector valued Boolean functions (2018), https://doi.org/10.1016/j.tcs.2018.02.023
- The multiplicative complexity of quadratic boolean forms (1992), https://doi.org/10.1016/0304-3975(92)90235-8
- Bu, Fan, Joo, Minimum Synthesis Cost of CNOT Circuits (2024), https://arxiv.org/abs/2408.07898
- Webster, Koutsioumpas, Browne, Heuristic and Optimal Synthesis of CNOT and Clifford Circuits (2026), https://doi.org/10.22331/q-2026-09-21-2212 (related; also cited in earlier work)
- Li et al., Parallelizable Exact Synthesis of Quantum Circuits via Semi-Tensor Product (2026 preprint), https://arxiv.org/abs/2607.24195
- Boyar, Peralta, Pochuev, On the multiplicative complexity of Boolean functions over the basis (AND, XOR, 1) (2000), https://doi.org/10.1016/S0304-3975(99)00182-6
- AlphaTensor-Quantum (previously cited), https://doi.org/10.1038/s42256-025-01001-1

These support vector-output multiplicative complexity, alternating-rank decomposition and exact word search. Not claims of reproducing external solvers or new mathematical results. Actual Python, pinned parent files and KMB receipts are in the separate reproduction archive. No official verifier, no Kaggle submission, no main changes.
