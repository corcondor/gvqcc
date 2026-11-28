# V6: guarded phase hub + cross-session atlas/lifetime integration (NOT SUBMISSION)

Pinned parents: #31 e63fce27433c57d461de6f20015146c13bb97358, #32 564fa7980038033e320975afa6c0c2cae0009081. Common reference KMB SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03. Read #29, #30 and #33; the latter's partial [8288,9358) is not automatically additive. Main untouched. Two V5 ZIPs were retrieved from Library and independently compared.

## Measured results
- #32 virtual HMR edge [8215,8228) overlaps #31's exact atlas; do not count 13 ops again. #31 reconstruction at V4 emitted op47113 overlaps #32's q25 donor. Exact two-disjoint-lifetime donor splice into #31 wide: 1879 -> 1877 static, 1705.3125 -> 1703.3125 expected, 53195 covered, 62638 exact paired comparisons PASS; SHA256 6a560bac6573861684561dd666360d19d12b549356760470edfe844e274555f3.
- New guarded Clifford block compiler collects ANF phase through complete affine identity IF scopes, rather than destroying a relation at each guarded CX. 94 unresolved gaps screened, 5 candidates, only 1 initially accepted (253 original ops). Exact source-state filter: 193 sampled relations on 5 gaps, 133 false, 3 corrected candidate edges passed [13954,13991) (+2 static), [44915,45168) (+9), [46284,46548) (+17). No acceptance based solely on sampled masks. New 554 source ops.
- Verified full serialized 37Q diagnostic wide: 53749/60766 covered (88.452424%), 7017 remain, 129 chart intervals, 1907 static / 1724.3125 expected, 43264 exact composition checks PASS, SHA256 278b26c7a0f463d7b38bd8a9e11195138edec46feca4a0d3d24b2109fd201cc8.
- Separate exact guard-pooling on first phase-wide candidate: 1428 diagonal guarded blocks, one pair (classical 806,808) pooled. 1888 -> 1887 static, 1712.3125 -> 1711.8125 expected, 53448 covered, 62599 exact comparisons PASS. Hash b5d47851f053827a54fa2a7ddded82cdf8b9bf2797a30fe5eae4fe9bf3f0276f.
- New cost/coverage DP over 27 disjoint exact edges from #31 + V6: 122 nondominated static-budget points. Relative to V4 budgets +10/+25/+50/+100/+151 yield 52068/52471/52911/53568/53749 covered source ops. Static budget is not official expected cost; selected programs need full BDD.
- No full 36Q circuit, official verifier PASS or score update. Lean file certifies Boolean identities and the actual source fragment [44933,44945), not full oracle. CI required before claiming it passes.

## Reproduction with the separately supplied V6 source bundle
Extract the V6 zip, cd central/global_chart. Execute:
```sh
python v6_phase_blocks.py
python v6_verify_phase.py
python verify_portfolio.py v6phase_wide
python v6_exact_fresh.py
python v6_verify_filtered.py
python verify_portfolio.py v6filtered_wide
python v6_frontier.py
python verify_portfolio.py v6budget25
python v6_final_integrate.py v6filtered_wide
```
Only use trusted pickle files. The repo core snapshot is excerpted from the actually run implementation; standalone bundle contains original KMB, all scripts and receipts. Keep #30 open-chart and #33 partial data separate until their source interval and ABI verified against the selected path.

## Additional citations (in addition to references in #29, #31, #32)
- Amy & Lunderville, Linear and Non-linear Relational Analyses for Quantum Program Optimization (POPL 2025), https://doi.org/10.1145/3704873 — V6 guarded whole-scope relational compiler; already cited by #31.
- Chen et al., PhasePoly (2025), https://arxiv.org/abs/2506.20624 — multi-block phase synthesis.
- Amy, Towards Large-scale Functional Verification of Universal Quantum Circuits (2018), https://arxiv.org/abs/1805.06908 — symbolic sign/transition semantics.
- Hietala et al., A Verified Optimizer for Quantum Circuits (POPL 2021), https://arxiv.org/abs/1912.02250 — candidate-specific verification and compiler trust.
- Duncan et al., Graph-theoretic Simplification of Quantum Circuits with the ZX-calculus (2019), https://arxiv.org/abs/1902.03178 — nonlocal simplification; future.
- Kissinger & van de Wetering, Reducing the number of non-Clifford gates in quantum circuits (2020), https://doi.org/10.1103/PhysRevA.102.022406 — phase sharing and nonlocal cancellations; PyZX https://github.com/zxcalc/pyzx (reference, not a claimed run).
- Amy, Maslov & Mosca, Polynomial-time T-depth Optimization via Matroid Partitioning (2014), https://arxiv.org/abs/1303.2042 — resource scheduling inspiration; future.
- Draper et al., A Logarithmic-depth Quantum Carry-Lookahead Adder (2006), https://arxiv.org/abs/quant-ph/0406142 — alternative carry architecture; future, ancilla cost must be respected.
- Amy & Stinchcombe, Polynomial-Time Classical Simulation of Hidden Shift Circuits via Confluent Rewriting of Symbolic Sums (2025), https://doi.org/10.22331/q-2025-12-02-1926 — exact rewriting/verification inspiration.

## Handoff
Use #31 exact atlas and #32 two non-overlap donors, do not repeat failed fresh-sample candidates. Prefer guard coefficient sharing (classical GF(2) phase coefficient matrix), scope-aware exact relations, and low-cost macro search on 7017 remaining source ops. Do not optimize coverage alone; full 36Q must beat 37Q expected official costs and independently pass.
