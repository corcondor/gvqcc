# V56: bounded-width nonlinear multiplexing, persistent affine transport and carry-save phasing (research only)

No submission, no main branch changes. Every emitted full circuit uses 28, 30, 34 or 36 qubits. Parent PR128 rounded spectral phase; use PR130 tensor factorizer as donor. All 2^22 controls, input/scratch restoration, all independent HMR sign coefficients, exact modular phase and all 3,133,452 legal inputs (squared integer tolerance) pass independent serialized replay. This is **not** official verification or a competitive score. Worst relative error / tolerance = 0.8125815968960524.

| Variant | Q | CCX | Generic rotations | Native ops |
|---|---:|---:|---:|---:|
| count36 | 36 | 34625 | 3548 | 540220 |
| fused34 | 34 | 27332 | 3945 | 504151 |
| fused30 | 30 | 24797 | 4579 | 441041 |
| fused28 | 28 | 22880 | 5421 | 389570 |
| lazy36 | 36 | 25134 | 4250 | 285170 |
| mux36 | 36 | 29345 | 3770 | 361342 |
| direct36 (matched partition) | 36 | 28958 | 4103 | 355093 |
| hub36 (matched partition) | 36 | 28614 | 4103 | 332691 |
| cost34 | 34 | 26885 | 4169 | 299268 |

New implementation: equal-angle count compression using carry-save triples/septuples, HMR retirement of temporary affine leaves, onehot prefix multiplexing of quadratic factors, and persistent quotient-basis transport between rotations. Matched hub/direct comparison: -344 CCX, -22402 ops, same target, cluster partition and rotation count. HMR increases (6967 to 8338); phase debt verified. Hub statistics: 4103 requests, 44 exact cache hits, 4128 delta rows, 6906 new rows, 759 basis-change CX. No claim of global optimality. A fixed proxy Q(CCX + (239.00391117857393/33)*R) is 1738818 for fused30 vs 1911729 for PR130 angle-carry and 1760013 for PR131 Q25. Per-angle synthesis precision is not modeled. Far from incumbent 60927.55; lower rotation count must be achieved without excessive paid arithmetic. PR132's 31-rotation mathematical specification and 26Q normalization / 33Q coefficient stream are a different architecture and are not yet a full integrated oracle.

Lean checks local universal Boolean/integer identities only; complete serialized replay is separate. Full native artifacts, executable Python compilers, receipts and reproducibility commands in the research conversation archive. All candidate generation caps width at 36, not just the final header. Do not add independent parent-lineage savings or use 37Q as a new candidate.
