# V43 — hard physical-36 tensor path synthesis

Research only / NOT SUBMISSION. Both complete hybrid circuits remain 37Q. The objective for feasible paths is expected native paid gates + physical ops/1000. A strict 36-slot arc must preserve data, relative phase, rotations, classical records and activation, including every zero scratch operand and HMR event. The graph is incomplete, and no end-to-end feasible path exists in this tested candidate library. Disconnected fallback is a separate diagnostic optimizing blocked source operations, with optional exact paid budget.

| parent | ops before → after | expected paid before → after | 37-nonzero cuts | blocked source edges | strict reachable source prefix / physical ops |
|---|---|---|---|---|---|
| PR104 wide | 41921 → 42061 | 26047/16 → 26255/16 | 2620 → 2557 | 2736 → 2665 | 8644 / 8556 |
| PR97 compact | 41950 → 42077 | 23095/16 → 23223/16 | 3149 → 3099 | 3415 → 3356 | 6581 / 6503 |

Both independently re-read serialized KMBs and exact replay PASS on 3,133,452 legal inputs, respectively 1276 / 1278 independent HMR bits. Wide SHA256 8ec36238f3b015df47427bae77fc330409f1994ab33634d32d36c43e831e35a4; budget SHA256 c45da54830e940346aea3d5fd56c6fafa8f9181a81c672f4459bec5741ed1da7. Wide 109 physical spans cover 39256 original ops; budget 258 spans cover 38594. Scope-free five largest fragments emitted with physical 36Q header, entry/exit maps; not standalone oracles. Wide prefix SHA e5f493cf16833ea6acfebb614accb5635b7ce57a04927962c52927ed41d10cc2. Prior wide prefix 6322 source ops. Next reachable frontier 8644, source CCX(33,27,36); no universal width impossibility proof.

## Joint factor and phase
Wide [6314,6340), budget [6318,6344): original 26 ops and 3 paid → 43 ops and 4 paid. Transport the factors of idle q9's original CCX through intermediate carry updates. At terminal q=R xor d xor c, R=L xor AB; c=q8, d=q35, output y=q36. Keep one affine factor gauge across data updates and measured-phase correction; no q9 storage. Compute c'=c xor R; y'=d xor ((not d) and c'); measure c' with source final q measurement record mc, add mc R, restore c=d xor R; measure d with md. Thus mc(c xor R) xor mc R = mc c. Event reordering explicitly aligned and verified. Physical 36-slot execution PASS. A separate lazy-only arc delays generation of q9 over a carry exchange with no paid overhead. Both are alternatives, not additive. Strict 36Q prefix uses the cross-stage arc.

## Candidate screening
PR105 exact word transfer, zero-coin retiming, native deferred product and cross-stage arc. Wide 21 candidates, 17 exact physically feasible, 4 semantically equal but require transient 37th slot; compact 39 candidates, 30 feasible, 9 fail physical. Four wide and nine compact direct donor candidates required presampling of original zero HMR on verified earlier free slots. Wide seven selected, compact eight selected with +8 E. Rank-one whole-episode synthesis screened 24 runs (23 quotient failure, 1 unsupported); dual measured-pivot restoration screen 40 pivots, no fit. Restricted failures only.

## References and scope
Reqomp, reversible pebbling and memory-constrained tensor contraction motivate arc feasibility and cost; not direct implementations of their results. corcondor/math family 379 inspires transport cost, no asymptotic theorem imported. Lean proves the local Boolean identities, not the complete circuit equivalence. Python exact BDD/native mapping verifies concrete arcs and serialized hybrids. Full source dependencies, scan JSONs, KMBs, and replay receipts in companion archive. No official verifier, no score claim, no main/Kaggle changes.
