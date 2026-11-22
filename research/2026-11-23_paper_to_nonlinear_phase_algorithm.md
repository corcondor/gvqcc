# Nonlinear relational phase synthesis: literature-to-implementation (2026-11-23)

The previous approach of searching neighboring CCX merges did not improve the ANGLE family. In contrast, the present independent invsqrt rewrite is **a global phase-relocation search**, not a CCX rewrite. The following papers establish the theoretical route, but do not themselves supply our circuit-specific replacement indices.

## Amy and Lunderville, POPL 2025
[Linear and Non-linear Relational Analyses for Quantum Program Optimization](https://doi.org/10.1145/3704873), article 37, PACMPL 9 (published 9 January 2025). [arXiv 2410.23493](https://arxiv.org/abs/2410.23493)

The paper reformulates phase folding as a relational analysis of classical pre-/post-state supports; §4 introduces affine relations, §5 extends to nonlinear polynomial relations via ideals/Gröbner bases, §6 uses sum-over-paths to infer transition relations. Its key design condition is that a phase conditional on a function of an earlier state may be transported across a circuit if the corresponding phase predicate has the same value on every state in the later support. This is precisely why physical adjacency of rotations is unnecessary.

**Our instantiation:** compute exact reachable Boolean masks of every live wire on all 3,133,453 supported invsqrt inputs, track 56 non-Clifford/phase operations through the 60k-operation KMB, identify signed 3T parity gadgets and locate an **earlier existing** wire equal to the corresponding nonlinear AND product. The two found witness wires are q36 after source operation 8344, and q35 after 8145; the original gadgets are around 32662 and 34341. This is different from implementing Gröbner basis or general sum-over-paths; our full-domain bitset representation is exact on the supported classical input domain and specialized to reversible arithmetic plus measurement-reset. Nonlinear classical arithmetic (CCX) creates useful temporal features which linear-only affine matching misses.

## Ruiz et al., Nature Machine Intelligence, 2025
[Quantum circuit optimization with AlphaTensor](https://www.nature.com/articles/s42256-025-01001-1), volume 7, 374–385 (published 20 March 2025); [research code](https://github.com/google-deepmind/alphatensor_quantum).

They minimize fault-tolerant T count by extracting a symmetric signature tensor and searching low-rank Waring decompositions, with gadgets that trade resources. This motivates global circuit-level synthesis and cost-measured gadgets rather than greedy local rewrites. **Our current code does not implement AlphaTensor, reinforcement learning, Waring decomposition, or claim their bounds.** It instead uses pre-existing computed Boolean features to replace 3T phases with an S phase, avoiding extra ancillas.

## Actual algorithm and failure boundaries

1. Parse KMB v2 losslessly and pin the parent SHA256.
2. Follow every classical wire's Boolean mask over all legal x values. For HMR, reset the measured input wire in the data representation; verify no measurement-conditioned *data-changing* gate occurs before the last phase edit (at op 34344). Conditional diagonal corrections remain unchanged.
3. For each 3T gadget, prove `f_a XOR f_b = f_c` and compute the signed phase function mod 8; search all earlier live wires for its nonlinear product mask.
4. Replace two gadgets with Clifford S gates on earlier wires; retain all data-changing gates exactly, use a separate negative-control sign-flip.
5. Prove the **entire phase difference modulo 8** is identically zero on all supported x values **before** the first classically conditioned data gate (op 35378). Native KMB parser roundtrip/byte-preservation additionally checked. Keep a separate out-of-domain control, which reports six mismatches for the combined edit on all 2^22 inputs.
6. Cost and correctness remain distinct: 9 T-type operations removed in the combined version (six from our own method, three from a public prior edit), **0 CCX removed**, 37Q retained. Official KickMix/Kaggle verification has not run; no score claim.

The third late 3T gadget (source indices 35289,35290,35292) did not have an observed pre-existing live-wire AND product in the bounded index/sampled-screen search; that is **not** a lower bound on alternative decompositions.

## Reproducibility

- Circuit generator: `research/invsqrt_nonlocal_phase_patch.py`; parent SHA256 `d2148a7c…`, candidate SHA256 `f9f00359…`.
- Standalone source, negative tests, full-domain proof and receipt are in the separately produced research ZIP (not committed as a binary).
- Candidate 18-file ZIP SHA256 `445d03f9…`, 17 original files unchanged; **unverified**.
