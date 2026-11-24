# V5 shared lifetimes and virtual HMR — diagnostic, NOT a submission

## Exact parent and reproducibility
- Source SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03 (60676? no: exactly 60766 source operations).
- V4 PR #29 commit f093af5fbc86298a272bf5498f7f799e4c29cd21, serialized diagnostic parent ca39e8c1bf363dd0909b37c4bc34f7f2aaad2926989469e3bd4399f041ff114d.
- V4: 51712/60766 source operations in 36Q charts, static/expected paid 1756/1609.3125.
- A: nonadjacent write-only lifetime compression. 711 epochs, 41 sample hits, 34 exact endpoint hits, 2 disjoint selected donors; 15 -> 13 paid. 62367 exact comparisons with all 3133452 legal inputs and 1186 independent parent-plus-extra measurement variables. Actual 37Q diagnostic SHA 0522af9ea336d887aa9bce01e1651c502645c22428c985ee371499f72b0d4113. Static 1754. No recounted source coverage. Concrete donors in lifetime_v5_donors.json.
- B: phase-ledger-aware nonlinear chart transport, 60 remaining gaps eligible, 1 accepted interval [8215,8228) with HMR 8227 removed. All gates in new chart body use physical slots <36. 45314 full source-composition checks PASS. Static/expected 1757/1610.3125, 51725/60766 source operations covered (85.12161406049435%), 9041 remaining. SHA b2131f40ba0b0f0a7c04932b006733ac891ff1b4ac732ac587ee9cd209937529.
- C: independent endpoint decoders on 1395 read-free spans, 4 sample variants, 6 exact endpoint checks, no accepted variants. D: quadratic quotient rank annealing, 30000 trials per each selected endpoint, rank 8 and 5 unchanged. Do not repeat identical search operators.
- Lean: phase compensation and actual factor-coefficient sets (8+5 factors). Lean proof scope is local algebra/coefficients, not full reachability or quantum-channel semantics.
- No claim of complete 36Q or official score improvement. The public 37Q source has expected paid 1406.3125. Never add #30 open-chart savings to #29/#31 without closed-state restoration and exact composition.

## Reproduce
Full Python scripts, source, V4 dependencies, KMB and BDD receipts are in the chat-generated V5 diagnostic archive. Place virtual_hmr_v5.py in central/global_chart of the V4 bundle, run python virtual_hmr_v5.py then python verify_portfolio.py v5virtual. Only load trusted pickle files. The new branch is stacked on #29, not main. #27 phase ledger and #28/#30 donors are separate; overlapping donors must not be double-counted.

## Additional literature (8 beyond V4's 8)
1. Bennett, Time/Space Trade-Offs for Reversible Computation (1989): https://doi.org/10.1137/0218053 — reversible pebbling, global space/time tradeoff.
2. Ding et al., SQUARE: Strategic Quantum Ancilla Reuse (2020): https://arxiv.org/abs/2004.08539 — ancilla lifetime and uncomputation schedule.
3. Paradis et al., Unqomp (2021): https://doi.org/10.1145/3453483.3454040 — dependency-aware inverse synthesis.
4. Meuli, Soeken, De Micheli, Xor-And-Inverter Graphs for Quantum Compilation (2022): https://doi.org/10.1038/s41534-021-00514-y — shared AND and qubit/T cost optimization.
5. Häner and Soeken, Lowering the T-depth of Quantum Circuits via Logic Network Optimization (2022): https://doi.org/10.1145/3501334 — ESOP cuts and dynamic programming.
6. Venev et al., Modular Synthesis of Efficient Quantum Uncomputation (2024): https://arxiv.org/abs/2406.14227 — compositional IR for uncomputation.
7. Ruiz et al., Quantum Circuit Optimization with AlphaTensor (2024; journal 2025): https://arxiv.org/abs/2402.14396 — tensor decomposition and reinforcement learning.
8. Zhang, Li, Ying, A Divide-And-Conquer Pebbling Strategy for Oracle Synthesis in Quantum Computing (2025): https://doi.org/10.1109/TCAD.2025.3570608 — hierarchical pebbling, width-aware synthesis.

These references motivate operators and future experiments, not a claim of reproducing external benchmark savings. V4's DeepMind Lean, QAOA, Gidney, Cuccaro, Luongo, Reqomp, MBUndo, and error-correction perspective remain cited in #29.
