# V10: moving-frame vector shear and shared decomposable atom synthesis
Research only. No main merge, no Kaggle submission. Both full circuits still require 37Q.

## Parents and exact native results
- Cost parent is PR51 archive's additional PR50-integrated candidate (not PR51's earlier 1865T branch), SHA256 e314ab93bb92b68e5e82898fec7fe85eff030e3a9627fe1fcba470ffbf78b30c, 42144 ops, 1863 static/1693.3125 expected paid, 55485/60766 source coverage.
- Moving-frame cost: c504e2b21936d6aa0b539b8005efdc6f8017cf677aa00c8c38c51dae231ac92a; 42149 ops, 1862/1692.3125. Full paired BDD PASS, 42124 comparisons, 1174 HMR variables.
- Final cost: 5037dc3fbe2025d53dd6010f68a6d9b95dc9bb681cc9f3bb3fc6b8dde47cedc7; 42151 ops, 1860/1690.3125. Full paired BDD PASS, 42133 comparisons, 1174 HMR variables.
- Wide parent PR51 cofactor: 5a35e7a5126dcbf979288c0cc8ad4f1c38af8729cbd591d0ccfc917a831fc9a0; 43161 ops, 1899/1718.3125, 55829/60766 coverage.
- Moving-frame wide: 358a1822a9bc4ee8a8bb777acb48188671bb68423347063dfc7387d430ca79c8; 43170 ops, 1895/1714.3125. Full paired BDD PASS, 43113 comparisons, 1186 HMR variables.
- Final wide: 6c59fd72e0684836c86776dc36c7a42b8c86a308257d8a78fc9cb6772ac87cc9; 43172 ops, 1893/1712.3125. Full paired BDD PASS, 43163 comparisons, 1186 HMR variables.

All BDD runs cover 3133452 legal inputs and all independently symbolic HMR outcomes; paired state, phase, rotation, active and classical memory/stack comparisons, clean output. Universal 37-bit ANF checks for all six selected pure reversible slices. Chart physical wires <36 checked after each rewrite; no new source coverage. Original rotation/target data retained by native emitter. Official verifier not run.

## Structural change (not another fixed-target/controls search)
Conjugate nonlinear operations into a moving affine frame, with vector update v A(x)B(x). Enumerate commutation-safe multi-target, multi-control groups, choose dual output basis by rank-weighted matroid greedy. Re-emit on existing physical coordinates and certify exact ANF. Then use a catalog of decomposable polar forms on invariant control subspaces, including provision for quotient-coset extensions; accepted examples required no extra span dimensions, nonzero-extension benefit not established. Incremental nonlinear-word endpoint ANF through up to 31 paid gates, explicit resource cap; no positive nonlinear-word collapse found.

Cost moving: 198 regions/3456 families/92695 dual probes/736 noncommuting word tests, one admitted rewrite. Wide: 294/3540/93375/796, three disjoint admitted rewrites (5 universal candidates).
Atom stage cost and wide: 1966 and 2013 deep-word checks, 83 and 96 cap exits, 3907 atom probes each, one admitted 3-to-1 CCX family each. All selected ranges use <=36 wires. Do not repeat fixed-frame single-target search, moving-frame family search, same polar catalog or same nonlinear-word cap with seed changes.

## Formalization and sharing
MovingTensorV10.lean contains six actual old/new gate lists, universal BitVec 37 equivalences and paid-count/wire obligations, not a formalization of the full native parser, BDD, HMR engine or official scorer. CI separately checked. Reproducible archive includes scripts v10_moving_tensor.py, v10_atom_extension.py, v10_replay.py, pinned parents, four staged native outputs and receipts, verifier dependencies. Preserve parent hashes; never transfer by arithmetic addition of gains.

## Additional references and relevance
- Mori, Hakoshima, Fujii, Nontrivial Multiproduct Commutation Relation Toward Reducing T-Count in Sequential Pauli-Based Computation (2026), https://doi.org/10.1103/qw5z-3bwz . Motivation for collective, rather than pairwise, identities; different gate model, not an implementation of MCR.
- The multiplicative complexity of quadratic boolean forms (1992), https://doi.org/10.1016/0304-3975(92)90235-8 . Alternating polar rank / 2 for single quadratic form, not an exact multi-output cost.
- Byrne and Cotardo, Constructions of perfect bases for classes of 3-tensors (2024), https://doi.org/10.1016/j.laa.2023.11.019 . Rank-one containing spaces motivate atom catalog.
- Boyar and Find, Multiplicative complexity of vector valued Boolean functions (2018), https://doi.org/10.1016/j.tcs.2018.02.023 . Multi-output AND sharing, not a native-width proof.

Conditional score model from PR43: cost E=1690.3125 -> 31.45690959 at 37Q, 31.74552121 hypothetical at 36Q; break-even E<1452.05390236 (need >238.25859764 additional expected paid reduction). Wide hypothetical 36Q 31.62585028. Score 34 requires E<=1331.15423976 at 36Q with all other costs fixed. No official score claim.

Residual 36Q gaps remain (5281 cost, 4937 wide source instructions); this pass does not close them. ANGLE historical code audit still incomplete: no new ANGLE search.
