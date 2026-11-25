# V46: affine/phase tensor synthesis — NOT SUBMISSION

Same-parent V41 input SHA256 553f46ba954f4c306f4fbd1080342e2faffe1ef9ba800656e480b3d69ddec54e.

| Variant | Ops | Full-37 cuts | Runs | Expected paid | HMR |
|---|---:|---:|---:|---:|---:|
| V41 |41533|2899|259|23143/16|1280|
| V46 phase tensor |39683|2835|259|23143/16|1280|
| V46 advance direct |39683|2822|259|23143/16|1280|
| V46 integrated |39688|2778|258|23175/16|1281|

Native SHA256: phase tensor cc2b7bb9c5106f572bbe4cfd8dd4d97bacb5d8634de19b77bb3a68862982c3a0; advance direct 98c33765002fc6b9e6e61881a4da766e111575140104f29981018470b028f822; integrated c8e6813e4fd5b5d56ef8af117d2770d58f3a087bb9e49824845824aea7b8ca15.

All three serialized replay PASS over 3,133,452 legal inputs and symbolic measurement events, phase/rotation/classical state checks and restored input. Full cuts count nonzero Boolean functions; NOT a minimum-width theorem. Width remains 37. No official verifier/score, no learning, no main/Kaggle update.

New simultaneous affine/phase tensor transport: 1215 windows, 3959 anchors, 2588 congruence trials, 4305 shears, 357 accepted blocks. Classical guard hubs accepted in 12 blocks. Integrated same-parent advance [19818,19832): 13->0 full cuts, 14 ops, zero paid change, still references q36. Parking [24740,24785): 44->0 full cuts, 45->50 ops, +2 expected paid, no q36 references. These two changes reverified together with fresh serialized event permutation and phase ledger. No additive claim across other PRs.

Negative results: common affine-intersection tensor synthesis, 771 windows, 209991 quadratic columns, 5589 RHS solves, four sampled candidates (same window) rejected in exact BDD. Conditional cofactor 135 motifs and queries, zero fits. Rank-one transfer: 41 reset candidates, 17 barriers, 24 rank-36 projections, 23 nonlinear direction/control collisions, one data-only body, no accepted phase solution. These are restricted classes, not global infeasibility proofs.

Finite matrix/Fourier audit: 7865 congruences exact match; counted nonzero-word XOR operations 52055->45143 using block row-subset memoization (13.28% reduction, NOT wall-clock or physical gate count). 1946 exact integer Walsh spectra, 476964 evaluation points, support cardinality 2^r where r is alternating GF(2) rank. No new asymptotic theorem implementation.

OpenAI/math fork pinned at 3344da59991ed94f9ba711217b29c1d760badfa6: [family 379](https://github.com/corcondor/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/docs/379.md). Read selected Lean theorem files, not full transitive proof audit. Claimed matrix exponent 9/4 over fields, not a width-constrained circuit bound. Fourier theorem requires group order invertible in coefficient field and appropriate roots; not directly valid for even Walsh over GF(2). Independent-batch theorem does not grant free shared computation. Our finite methods use ordinary GF2 tensor congruence and integer Walsh checks.

Local algebraic Lean certificate CI PASS: https://github.com/corcondor/gvqcc/actions/runs/45606448205 . This is separate from native replay.

Reproducibility archive delivered in research conversation: GVQCC_V46_AffinePhaseTensor_NOT_SUBMISSION.zip, SHA256 0d8e0153b95cc7b548f700121f7d3872db85528dd032163a9a4baeaa53dfa860 (276 files). Contains actual generators, native KMB variants, selection receipts, independent replay scripts, SHA manifest, failed-screen logs, engine and Lean sources. Main scripts v46_phase_tensor.py, v46_common_tensor.py, v46_rank_one_transfer.py, v46_cofactor.py, v46_matrix_fourier_audit.py, v46_integrate.py.

Coordination: reviewed #97, #100, #102, #103, #105-108. Compared against PR106 common-ancestor result (2786 cuts, E1451.4375); do not add gains directly. Future nonmonotone search should work on a globally transported nonlinear gauge and settle phase debt, rather than assume an endpoint rank certificate is a circuit. Whole 36Q remains open.
