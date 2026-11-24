# V5 adaptive nonlinear atlas

Parent: PR #29 (V4), commit f093af5fbc86298a272bf5498f7f799e4c29cd21. Related: #24–#28. Do not merge or submit: no complete 36Q oracle or official score gain.

## Reproducible evidence
Source 37Q SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03. V4 hybrid SHA256 ca39e8c1bf363dd0909b37c4bc34f7f2aaad2926989469e3bd4399f041ff114d.

- Fresh quadratic relations screened at 1,051 source cuts; 1,783 candidates, 1,264 after second sample. 32 macro candidates, 24 exact BDD-accepted on 3,133,452 legal inputs and 1,278 source potential HMR variables. 1,483 new original instructions covered by actual 36Q macros. 8 rejected. Wide path 53,195/60,766 (87.54%), 1,879 static paid vs V4 1,756. Exact edge results, not by themselves a whole-circuit certificate.
- Separate measurement-reconstruction branch: V4 emitted CCX(24,28,25) at index 47113 replaced with HMR and phase-compensated affine reconstruction of q25 = q13 XOR q18 XOR q19 XOR q28 XOR q29 XOR q34. New measurement outcome independent, never selected. 62,483 paired exact composition checks, 3,133,452 legal x, 1,185 candidate potential measurement variables. Static paid 1,756 -> 1,755, expected 1,609.3125 -> 1,608.3125. Candidate SHA256 9d3df69b3e6943fed1b029c71a5a52b5159d1f159838f54609b010499f05a87a. Still 37Q diagnostic; don't count reduction twice.
- Same reconstruction scan on the 37Q public reference: no exact accepted candidate. Backward terminal quotient: 5,109 cases, no viable macro. Do not repeat unchanged.
- Lean file AdaptiveAtlasV5.lean proves conditional reconstruction identity including arbitrary measurement sign and chart exchange. Actual global invariant is supplied by independent BDD rather than a Lean full-oracle theorem.

Reproduction in the V5 ZIP (contains V4 dependencies and input KMB):
```sh
cd central/global_chart
python v5_fresh_charts.py
python v5_verify_atlas.py
python verify_portfolio.py v5atlas_wide
python v5_reconstruction.py portfolio_v4context_300_hybrid37_NOT_SUBMIT.kmb v5_reconstruction_wide_NOT_SUBMIT
```
Pickle files must only be loaded from trusted archives.

## Literature / code provenance
These are research directions and references, not claims of copying implementations or running QAOA.
1. Shirobokov et al., *Discovering formally verified quantum programs with AI*, https://arxiv.org/abs/2611.09822 ; https://github.com/google-deepmind/formal-quantum-computation/tree/489edc7039aa4cdded53724b39ea90e33d2c88b4 — formal discovery / resource certificates.
2. Ichikawa et al., *Optimal elemental configuration search in crystal using quantum approximate optimization algorithm*, https://arxiv.org/abs/2503.09356 — combinatorial search; V5 uses classical beam DP, not QAOA.
3. Gidney, *Halving the cost of quantum addition*, https://doi.org/10.22331/q-2018-06-18-74 — measured uncomputation.
4. Cuccaro et al., ripple carry, https://arxiv.org/abs/quant-ph/0410184.
5. Luongo et al., measurement-based uncomputation for modular arithmetic, https://arxiv.org/abs/2407.20167.
6. Paradis et al., *Reqomp*, https://doi.org/10.22331/q-2024-02-19-1258 ; https://github.com/eth-sri/Reqomp/tree/fd2256e2643d6e0d3b3f07db225c979faebb6c69 — space/time tradeoff.
7. Amy and Lunderville, *Linear and Non-linear Relational Analyses for Quantum Program Optimization*, https://doi.org/10.1145/3704873 — adaptive relation analysis across control flow.
8. Meuli, Soeken, De Micheli, *Xor-And-Inverter Graphs for Quantum Compilation*, https://www.nature.com/articles/s41534-021-00514-y — nonlinear multiplicative cost.
9. Zhang, Li, Ying, *A Divide-And-Conquer Pebbling Strategy for Oracle Synthesis in Quantum Computing*, https://doi.org/10.1109/TCAD.2025.3570608 — hierarchical width optimization.
10. Xu et al., *Synthesizing Quantum-Circuit Optimizers* (QUESO), https://doi.org/10.1145/3591254 — algebraic rewrite synthesis and beam search.
11. https://arxiv.org/abs/2611.02345 ; https://arxiv.org/abs/2609.31605 — measurement-based uncomputation references retained from V4.
12. https://github.com/msoeken/reversible-sota — bibliography of exact reversible synthesis, no code copied.
