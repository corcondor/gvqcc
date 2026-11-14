# Research connected to the actual DQI circuit

These notes concern the public baseline whose SHA-256 begins `821bf8d157c0`, rather than an unoptimized reference circuit. Publication-time affiliations below were checked in primary papers. The experimental gate identities are our application of the research direction; they are not claimed as inventions of the cited papers.

## IBM / ETH: commutation-aware pattern matching

Raban Iten, Romain Moyard, Tony Metger, David Sutter, and Stefan Woerner, **Exact and Practical Pattern Matching for Quantum Circuit Optimization**, ACM Transactions on Quantum Computing (2022).

- [Primary paper](https://arxiv.org/pdf/1909.05270)
- [IBM Research publication page](https://research.ibm.com/publications/exact-and-practical-pattern-matching-for-quantum-circuit-optimization)
- Publication-time affiliations: Iten and Sutter, ETH Zurich / IBM Quantum Zurich; Moyard and Metger, ETH Zurich; Woerner, IBM Quantum Zurich.

The paper matches small circuit patterns while accounting for pairwise gate commutation. It applies to reversible X/CX/Toffoli circuits as well as general quantum gate sets. This explains why an adjacent-pair scan can find no applicable pair while a dependency-aware scan finds reductions.

Our first pass used the output-side identity, for four distinct qubits:

```text
CCX(a,b,x); CCX(a,b,y)
  = CX(x,y); CCX(a,b,x); CX(x,y)
```

The research review suggested checking its input-side counterpart:

```text
CCX(a,b,t); CCX(a,c,t)
  = CX(b,c); CCX(a,c,t); CX(b,c)
```

The target changes by `a*b XOR a*c = a*(b XOR c)`, and the control registers are restored. Both sides are the same basis permutation with no added phase. The identity holds for arbitrary input and target states, including superpositions. If a classical condition is present, all replacement gates need the same condition.

The actual baseline contains 16 previously unmodified blocks. Each has 36 CCX instructions and can be replaced by 12 CCX plus 48 CX, saving **384 CCX overall**. None of these intervals overlaps the previous 96-CCX reduction. All 16 blocks have condition-stack depth zero and no explicit classical condition, so the saving is exactly 384 per shot.

The basic identity was checked on all 16 four-bit inputs and both classical condition values. Every complete transformed block was independently compared using Boolean polynomials: each proof covers all `2^27` input assignments. The pass also rechecks commutation against the current rewritten sequence, including newly inserted CNOTs. Five regression tests cover the identity, operand ordering, interleaved product banks, forbidden measurement/reset/condition crossings, and rejection of an intentionally incorrect rewrite.

The read-only scan completed in 3.23 seconds with peak RSS about 153 MB. The standalone 384-CCX candidate build and both binary-layout checks completed in 29.57 seconds with peak RSS about 545 MB. These are local implementation measurements, not claims from the paper. Whole-decoder verification and Kaggle scoring are separate checks.

## Microsoft: dependency-aware cleanup and reversible pebbling

Alex Parent, Martin Roetteler, and Krysta M. Svore, **Reversible circuit compilation with space constraints** (2015 preprint).

- [Primary PDF hosted by Microsoft](https://www.microsoft.com/en-us/research/wp-content/uploads/2015/06/1510.00377.pdf)
- [Microsoft Research publication page](https://www.microsoft.com/en-us/research/publication/reversible-circuit-compilation-with-space-constraints/)
- The paper states that Parent performed the work as a summer intern with Microsoft's Quantum Architectures and Computation group; Roetteler and Svore were Microsoft researchers.

REVS combines mutable data-dependency tracking, in-place updates, early cleanup, and recomputation under a workspace budget. General dependency-graph schedules are heuristic; the work does not establish an optimal schedule for our circuit.

For this DQI circuit, the useful next experiment is to model the joint 24-output multiplication and its shared products. The two observed 12-bit output groups cannot be assumed independent. The currently retained parent inputs and HMR phase-correction dependencies must remain available until their uses have been discharged.

Optimize the actual competition objective `R * Q^2 * mean_Toffolis`. With unchanged error overhead R, a reduction from 889 to 888 qubits can tolerate roughly 0.225% more Toffolis; 889 to 877 can tolerate roughly 2.755% more. These are acceptance thresholds for a proposed schedule, not predictions that those qubit reductions are feasible.

## IBM / Stuttgart: constrained qubit reuse

Sebastian Brandhofer, Ilia Polian, and Kevin Krsulich, **Optimal Qubit Reuse for Near-Term Quantum Computers**, IEEE QCE (2023).

- [Primary paper](https://arxiv.org/pdf/2308.00194.pdf)
- [IBM Research publication page](https://research.ibm.com/publications/optimal-qubit-reuse-for-near-term-quantum-computers)
- Publication-time affiliations: Brandhofer, University of Stuttgart / IBM Quantum; Polian, University of Stuttgart; Krsulich, IBM T. J. Watson Research Center.

The work treats reset and qubit reuse as a constrained optimization problem, including a SAT formulation. It is relevant to converting our liveness observations into a legal schedule and allocation model. The 840 syndrome input qubits cannot simply be measured and discarded in DQI. Reuse candidates must be genuinely clean scratch qubits, and the model must include measurement records and the remaining phase corrections.

## Arithmetic and measurement context already present in the source

- Craig Gidney, Google, **Halving the cost of quantum addition**, Quantum 2, 74 (2018): [primary publication](https://quantum-journal.org/papers/q-2018-06-18-74/). Temporary logical ANDs can be erased using measurement and Clifford corrections. Our source already implements measurement-based cleanup and deferred correction masks, including a 66-Toffoli GF4096 inverse. A control that has been overwritten cannot generally be used as though it still held the original value for phase correction.
- Iggy van Hoof, TU Eindhoven, **Space-efficient quantum multiplication of polynomials for binary finite fields with sub-quadratic Toffoli gate count**, 2019/2020 preprint: [primary paper](https://arxiv.org/pdf/1910.02849). Ancilla-free Karatsuba scheduling is relevant, but the actual source already uses a 42-product GF4096 tensor and a 99-product GF(2^24) extension tensor. Replacing these with a generic Karatsuba routine is not an established improvement.
- Francisco J. R. Ruiz, Tuomas Laakkonen, and collaborators, **Quantum circuit optimization with AlphaTensor**, Nature Machine Intelligence 7, 374–385 (2025): [publication PDF via an author institution](https://ir.cwi.nl/pub/35964/35964.pdf). Affiliations include Google DeepMind, Quantinuum, and the University of Amsterdam. Tensor-decomposition search is relevant to a possible 99-to-98 product improvement, but the paper's T-gate/gadget objective differs from this competition's Toffoli-equivalent objective. Its reported GF(2^6) result uses 18 Toffolis, while this source already has a 15-product kernel.

The source confirms that the 42-product multiplication evaluates a cubic over GF(8) at seven points with six bilinear products per evaluation. The 99-product extension multiplication uses eleven GF(16) evaluations with nine products each. The product emitter already uses CNOT fanout around one CCX per product. Ordinary fanout, Karatsuba ideas and measurement-based uncomputation are therefore established baseline features; new improvements must be measured against them.
