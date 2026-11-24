# V36: joint carry quotient, rank-one fanout and cross-branch 36Q fragment

Research only — NOT SUBMISSION. No main/Kaggle changes. The V35 parent is PR86 SHA d873f84acb4a9afb5652f7f56597728953beb60d91afdb7262a6a4249e9f8274. PR87–90 were reviewed, including the independently developed PR90 three-stage 36Q fragment and PR89 economy parent. Do not count concurrent overlapping techniques as independent novelty.

## Exact verified artifacts
- V35 source: 161 carry motifs, 130 in one unconditional block. 24 care-set quadratic decoders, 22 global exact, 2 conditional-only exact (BDD over all 3133452 legal x and 1281 independent HMR variables). All 22 global decoders factor into one affine-factor product plus affine terms. Example at 7430: q35=(q13+q28)(q18+q28+q32)+q13+q18+q28. CNOT sandwich distributes one product to both targets without an additional product.
- 9 disjoint shared fanout splices: 51024->51088 ops, 3702->3675 full cuts, E1442.3125->1451.3125, 1281 HMR; independent serialized BDD replay PASS. SHA 496ab37734ee03bbb3c1011f713c19781be2a49ee33ac8d18fa5d1c34a92e08a.
- Cross-branch transfer: PR89 economy parent 2b49b859134cce45873a8477f19349e02fffd8f5d9c9822282342f6d5474b394; its [7429,7473) exactly matches V35 [7430,7474). PR90 compact 73-op donor efc2a6b1605a9d2c3a04d6ed691c47ef0582c81d51d38eb6ffc7a3c470263d5f. At first carry, presample original independent HMR 513 on initial clean q22 into unused record 1021; transfer record at source interval, update q35 in place, add rank-one decoder into q7, delete old HMR+seven phase correction terms whose joint sign is zero. Preserve the remaining two donor stages. 73->66 local ops, all on q0..35; 3-stage projected exact phase/data/rotation/classical/guard match. Full native re-read paired BDD PASS 3133452 x /1288 independent outcomes /51317 checkpoints. 51360->51383 ops, 3352->3343 full cuts, E1445.9375->1450.9375 (+5), static1596->1601. Native SHA 511525aeadbbac4d593f193ba70f28572b5dfe897ba41f66e97c0f261e763cb1. Not a global width frontier (PR89 budget has 3303 full cuts at E1451.9375), not whole 36Q. No direct 80-product savings, lowest E1406.3125 not beaten.

## Failed classes / bounded search
- Rank-tight hyperplane paths 305 joint windows; 5,146,508 factor probes, 2013 moves, no endpoint.
- Hybrid retiring HMR directions 305 eligible windows, 5,423,268 probes, 2005 reversible moves; no projection move / candidate.
- Nonmonotone quotient walk: bounded 180 windows, 907947 probes, 1461 expansions, 8252 reversible edges; no candidate.
- Backward required-affine liveness 2086 windows, 1752 fit rank <=36, no product saved in that fixed atom order. Rank count alone does not certify reversible synthesis or phase.
- 41 low-rank joint windows: one sampled candidate, no full-cut relief; not adopted.
- Active nonlinear loan: 161 starts, 5749 entry tests, 7 fits, no positive joint candidate. Dense known-decoder loan: 22 entry fits, no candidate.
- Moving pivot graph (distinct restricted search from PR89): 161 starts, 11366 switch tests, 215 sampled switches, no qualifying endpoint.
- In-place gauge carried over multiple motifs with no intermediate restore: 161 starts x3 modes, 50336 steps, 4018 joint endpoints, no sample candidate. Earlier broader variant interrupted; bounded results not global obstructions.

## Literature and implementation scope
- Khattar/Gidney, Rise of conditionally clean ancillae (Quantum 2025, https://doi.org/10.22331/q-2025-05-21-1752): conditional care sets and slot reuse; not claiming their complete construction was imported.
- Kornerup/Sadun/Soloveichik, Tight Bounds on the Spooky Pebble Game (Quantum 2025, https://doi.org/10.22331/q-2025-02-18-1636): measurement and deferred phase debt; implement presampling and exact phase settlement. Not a proof that their asymptotic bounds attain our paid target.
- Kumar/Perkowski, incomplete specification (QIC, https://doi.org/10.2478/qic-2025-0038): care-restricted synthesis; applied via GF(2) solving of actual reachable rows, not their QAS implementation.
- Yang/Al-Bayaty/Perkowski, Minimization of AND-XOR expressions with decoders (PRA May 2026, https://doi.org/10.1103/6vm9-21gr): decoder factor sharing, used public abstract's design principle and rank factorization; full article subscription-restricted, not implementation of butterfly algorithm.
- Shah/Fiszer/Perkowski, Factorized Boolean representations (https://arxiv.org/abs/2608.27430): affine-factor compression; also prior cited.
Lean 4.35.0 verifies Boolean factorization, care identity, in-place carry, fanout, pivot exchange, and GF2 telescoping. Reachable premises/native circuits separately verified by BDD. Full Lean oracle equivalence not proved. Full reproduction ZIP in conversation.
