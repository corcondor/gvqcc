# V9 global phase-syndrome compiler (research only)

Parent cost-first: PR #45, commit af62e8f38536ab2284cb652b9079ef1f6586c9b9; native SHA256 f7abc033dbed5477d5685225d9bf5fe262ceb888189ebcc3266ce23f9d15fd6d. Separate width-first donor PR #44 native SHA256 88932661d90e2f253a7845d550f657b2c26a062adfa54b05438c64ae8adea0be. Do not add their gains across distinct parents.

## Actual native KMB results

| candidate | native instructions | static paid | expected paid | original source coverage |
|---|---:|---:|---:|---:|
| PR45 | 42599 | 1875 | 1704.3125 | 55485/60766 |
| V9 phase equality | 42179 | 1873 | 1703.3125 | 55485/60766 |
| V9 cofactor | 42202 | 1865 | 1695.3125 | 55485/60766 |
| V9 syndrome | 42142 | 1865 | 1695.3125 | 55485/60766 |
| PR44 width | 47094 | 1914 | 1727.3125 | 55829/60766 |
| V9 wide phase | 43138 | 1907 | 1726.3125 | 55829/60766 |
| V9 wide cofactor | 43161 | 1899 | 1718.3125 | 55829/60766 |

Final cost-first SHA256 44605f0db084ee04dd56794934fc1d115ff6589457c33639f2ba75ffb51ac20c. Final width-first SHA256 5a35e7a5126dcbf979288c0cc8ad4f1c38af8729cbd591d0ccfc917a831fc9a0. Both are 37Q diagnostics, NOT submissions. Independent exact domain: 3,133,452 legal inputs; respectively 1,174 and 1,186 independent potential HMR events. Phase deletion has unchanged nonphase stream and exact zero GF(2) coefficient ledger; cofactor changes compared all state/phase/rotation/measurement data at each admitted replacement. No official KickMix run, no leaderboard update.

## New architecture and negative results

Canonical full-domain BDD signatures across different times and guards propose sign-phase deletions. Recheck using exact sparse transcript ANF ledger, independently of digest collision assumptions. PR45: 13,012 phase events, 205 equivalence classes, 420 deleted (2 CCZ), expected -1. Subsequent sparse syndrome basis selection groups by transcript-monomial support, free columns first. Screen 32,768 random legal inputs with independent symbolic HMR; 32 groups propose 1,324 deletions including 13 paid. Exact full-domain ledger admits 7 groups/60 free deletions; 25 rejected. No additional paid savings from sparse elimination. PR46 affine-cofactor method independently reapplied on both distinct parents: 8 unconditional CCX replaced by affine updates on each. Actual lists/conditional Lean lemmas provided for the cost branch.

95 residual gaps dependency-DAG retiming: first 2,280 trials / 2 sample hits / 0 exact; second (identity-aware after cofactor) 3,040 trials / 3 sample hits / 0 exact. No newly certified source coverage by V9, 91.87539% inherited from PR44. Guard refinement: 1,261,611 tests, 4 intersected sample candidates, no exact savings. Do not repeat identical screens with different seeds.

Conditional cost model (other two tasks and 240.37798500105055 rotation overhead fixed): S=33.17031640530013*(60927.54794503887/(Q*(E+240.37798500105055)))^(1/3). Cost-first hypothetical full36 score 31.71816414; still >243.25859764 expected paid reduction needed to break even at 36Q (E<1452.05390236). Depth metric: wire/classical dependencies and measurement/rotation serial order; cost parent 24644 -> 24339. Not hardware runtime, not score.

## References

- Bryant, Graph-Based Algorithms for Boolean Function Manipulation, DOI 10.1109/TC.1986.1676819 (canonical Boolean representation; exact ledger is independent of digest).
- Amy and Mosca, T-count optimization and Reed-Muller codes, https://arxiv.org/abs/1601.07363 (phase-code optimization inspiration; different cost model).
- Amy and Lunderville, Linear and Non-linear Relational Analyses for Quantum Program Optimization, https://doi.org/10.1145/3704873 (prior cited, relational phase folding).
- DeCross et al., Qubit-reuse compilation with mid-circuit measurement and reset, https://doi.org/10.1103/PhysRevX.13.041057 (prior cited, liveness/retiming).
- Modular Synthesis of Efficient Quantum Uncomputation, https://doi.org/10.1145/3689785 (hierarchical reversible deallocation).
- Structural Parallelism in Quantum Programs, https://doi.org/10.1145/3806645.3816162 (lifetime-guided width/depth optimization).
- Meuli et al., Xor-And-Inverter Graphs for Quantum Compilation, https://www.nature.com/articles/s41534-021-00514-y (prior cited, multiplicative cost).
- Ichikawa et al., https://arxiv.org/abs/2503.09356 (QAOA architecture inspiration, no QAOA executed here).
- DeepMind formal library https://github.com/google-deepmind/formal-quantum-computation (proof-oriented architecture, no external code copied).
- Peer code PR44/45/46/47: https://github.com/corcondor/gvqcc/pulls .

## Reproduction

Companion ZIP: verified native KMBs, source parent KMBs, exact receipts, executable scripts in merged/union/central/global_chart (v9_phase.py, v9_cofactor.py, v9_syndrome.py, v9_wide_phase.py, v9_wide_cofactor.py, v9_retime.py, v9_retime2.py, v9_predicate.py). Keep reference source and old archive modules intact. Main unchanged. Lean is algebraic and conditional concrete-gate certificates, not a full native semantics proof. No merge or Kaggle submission.
