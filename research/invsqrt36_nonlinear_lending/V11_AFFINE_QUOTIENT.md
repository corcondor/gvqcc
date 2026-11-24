# V11 nonlinear affine-quotient paths + measurement boundary + bounded bidirectional words

Research only; NOT SUBMISSION. Base #53 at 4553c673dcf422b7c4462183292be9b877bba1d9. Independent integration of #54 measurement-sink ideas into #53 native cost and wide circuits. #55 reviewed; do not add its separately derived gains. Main unchanged.

## Results (same public source SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03)
| parent | instructions | static paid | expected paid | source covered |
|---|---:|---:|---:|---:|
| #53 cost | 41816 | 1852 | 1682.3125 | 55485/60766 |
| V11 cost | 41333 | 1845 | 1675.3125 | 55567/60766 |
| #53 wide | 42767 | 1882 | 1701.3125 | 55829/60766 |
| V11 wide | 42294 | 1877 | 1696.3125 | 55829/60766 |

Final native SHA256:
- cost 75245d971b7e73ea8a91ba84985ee6e58a8f822cafd7547c0517ad1d5a1c74b7
- wide 1be6db376ef10b394d6c1a393f80f119123d7cdab7a05197907e285615496c79

Fresh independent direct source-to-final compositional BDD replay from the actual #53 native parents:
- cost: 39,706 comparisons, 350 exact changed source spans, all 3,133,452 legal inputs, all 1,174 original independent HMR variables, 1 removed event, exact expected paid 1682.3125 -> 1675.3125, PASS.
- wide: 41,045 comparisons, 274 exact changed spans, all legal inputs, all 1,186 original independent HMR variables, no removed event, 1701.3125 -> 1696.3125, PASS.

All source operations are executed; unchanged operations matched byte-for-byte and share equal entry state. Each changed span has both branches evaluated with aligned measurement event identities, comparing state, phase, classical bits, guard stack and rotation controls. Native non-operation sections identical. This is a computational-basis/phase BDD validation under the same KickMix model as previous PRs, NOT official verifier or full Lean oracle proof.

## New structures and integration

1. Instead of requiring pairwise invariant controls as #53, represent each reversible chart by the span of its coordinate truth tables and constant. A single CCX changes at most one direction of that span. For dimension deficit two, a shortest two-CCX path must pass through an intermediate span containing the common intersection. Enumerate hyperplanes containing that intersection, independent two-dimensional control subspaces, and exact degree-two alternating-rank checks at the second edge. This explores noncommuting nonlinear programs. Bound: <=7 active wires, <=8 original CCX per window, direct one-step for deficit one, two-step search for deficit two; no global optimality claim. Cost 652 windows/16,551 intermediate moves, wide 663/14,598; one exact 3->2 CCX rewrite on each. Preserve physical chart between moves instead of rebuilding arbitrary bases: original cost [6020,6034) 14->19 instructions (naive quotient realization 68), wide [6572,6587) 15->19 (naive 54). Full universal ANF, serialized native roundtrip.
2. #54-like measurement sink and virtual phase-only accumulator integrated into actual post-quotient streams, not additive receipts. Cost 4,210 backward visits/8 sink options/5 accepted sinks save 6 paid, plus source [26344,26426) (80->76 native operations) eliminates one HMR without conditioning on its result. Coverage 55,485 -> 55,567. Wide 4,182 visits/6 options/4 accepted sinks save 4 paid. All exact BDD comparisons passed; the 82 source operations are already covered by the width-first path and are not counted again. The measurement method is peer reuse, not an invented architecture.
3. Exact bounded bidirectional native affine-word search on 4-wire affine, 5-wire and 6-wire windows, rather than the earlier complete small Cayley tables. Enumerate identity-side depth 3 and target-side depth up to 3 (4/5 wires) or 2 (6 wires); X, CX and SWAP when applicable. Cost 20,854 windows, 1,461 positives, 348 nonoverlapping replacements, -484 instructions. Wide 24,350 windows, 1,364 positives, 274 replacements, -477 instructions. No paid change. All selected words universally ANF equivalent and exact BDD chain passes. No global depth or shortest-circuit claim. Multiple windows may be in the same source splice after composition.

## Lean and reproducibility
AffineQuotientV11.lean: six actual unconditional native gate-list equivalences and six resource proofs, plus the virtual82 phase-coefficient identity and sink phase identity. Does not formalize the entire BDD engine, all 622 affine edits, or the full HMR instrument. CI configured. Search core in v11_affine_quotient_core.py; full tested source and exact machine-readable native receipts are in the companion archive GVQCC_V11_AffineQuotient_1845T_NOT_SUBMISSION.zip. Run from its root: `python quotient_chart.py parents/cost.kmb parents/cost.json cost_chart`, `python integrate_measurement.py cost_chart/transport_NOT_SUBMIT.kmb cost_chart/transport.json cost_integrated --width`, `python mitm_affine.py cost_integrated/transport_NOT_SUBMIT.kmb cost_integrated/transport.json finalcost`, `python replay_chain.py parents/cost.kmb cost_chart cost_integrated finalcost finalcost/replay.json`; analogous wide with no --width. Preserve parent files.

## Further primary references
- Shende et al., Synthesis of Reversible Logic Circuits (2003), https://arxiv.org/abs/quant-ph/0207001 ; https://doi.org/10.1109/TCAD.2003.811448 — ancilla-free reversible permutation synthesis.
- Golubitsky and Maslov, A Study of Optimal 4-bit Reversible Toffoli Circuits and Their Synthesis (2011/2012), https://arxiv.org/abs/1103.2686 — bounded exact permutation synthesis.
- Aaronson, Grier, Schaeffer, The Classification of Reversible Bit Operations (2015/2017), https://arxiv.org/abs/1504.05155 — affine classes and reversible gate-generated spaces.
- Calik, Sonmez Turan, Peralta, The Multiplicative Complexity of 6-variable Boolean Functions (2018), https://doi.org/10.1007/s12095-018-0297-2 — affine equivalence classes and nonlinear cost.
- Calik, Sonmez Turan, Peralta, Boolean Functions with Multiplicative Complexity 3 and 4 (2020), https://doi.org/10.1007/s12095-020-00445-z — classification of low-AND-count functions, future deeper quotient search.
- Prasad et al., Data Structures and Algorithms for Simplifying Reversible Circuits (2007), https://web.eecs.umich.edu/~imarkov/pubs/jour/jetc07-loco.pdf — exact small reversible synthesis and compact lookup.
- Amy et al., A Meet-in-the-Middle Algorithm for Fast Synthesis of Depth-Optimal Quantum Circuits (2013), https://doi.org/10.1109/TCAD.2013.2244643 — bounded bidirectional synthesis (already cited elsewhere).
These works are relevant foundations, not a claim that their external algorithms were reproduced in full or that all references are unique across repository history.

## Stop conditions and cost target
No complete 36Q; actual max wire index 36 (37Q). Cost covers 91.4442% (5,199 source ops left); width covers 91.8754% (4,937 left). At full 36Q need E<1452.05390236114 under #43 model, another >223.25859764 expected paid savings for cost. Conditional model #43 predicts cost 31.53879954 at 37Q, hypothetical 31.82816249 at 36Q; wide 31.42439076 / 31.71270403. No official scoring, no leaderboard gain. Avoid repeating the same deficit-two and same narrow decoder search only with more seeds; next target larger coordinate quotient paths across noncommuting arithmetic and measurement instruments. Do not merge main or double count peer donors.
