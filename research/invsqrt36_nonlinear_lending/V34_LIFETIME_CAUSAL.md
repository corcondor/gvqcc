# V34: causal lifetime schedule and physical slot allocation

Research only / NOT SUBMISSION. The final combined native candidate has SHA256 `8039c8a9c33adaebb61c162b3057368431c8bfaa3418eecbec9f60d511c811e9`. V33 width parent 54244 ops, E1447.3125, 5167 full cuts; selective flatten + causal schedule 51712 ops, 3818 full cuts; slot allocation 51001 ops, same E and full cuts. Five PR83 donors transferred through original node identities, independent serialized BDD replay: 51730 ops, E1442.3125, 1281 independent HMR variables. Combined allocation: 51019 ops, E1442.3125, static1594, 3818 full cuts, whole width37. Exact BDD all 3133452 legal inputs, measurement outcomes preserved independently; allocation checks trajectory and serialized operations. 47495/51730 source ops fall within 297 physical <=36 spans, longest source length8838 (native 8742). Different denominator from V27 source coverage. Separate fixed parent: 8/11 donor matches, 54146 ops/E1437.3125/5264 full cuts. PR83 E1436.3125 is a different parent. Low E1406.3125 not beaten.

## Obstruction and failed searches
Width source: 298 observed 37-live lifetime sets, 294 forced under fixed conservative read/write DAG, 279 remain after relaxing quantum phase-only read edges. Each forced set has a common allocation/release hub. Not a lower bound on alternate encodings or circuits. 136 carry motifs failed sampled contextual quadratic screening; 23 clusters/508 spans/14458 parking choices/4488 distinct complete quadratic decoder checks/2670360 products yielded zero sampled fits. No accepted new parking rewrite. No claim of exact channel equivalence after dropping a source HMR. 

## Reproduction
Companion archive GVQCC_V34_LifetimeCausal_NOT_SUBMISSION.zip contains pinned KMB parents, engine, Python programs, receipts, logs and cached traces. Run from v30 directory:
- python v34_schedule.py v33_width_NOT_SUBMISSION.kmb hybrid v34_width_hybrid_NOT_SUBMISSION.kmb
- python v34_lifetime.py v33_width_NOT_SUBMISSION.kmb.flat.trace.pkl
- python v34_hub_certificate.py
- python v34_carry.py; python v34_park.py
- python v34_schedule_peer.py
- python v34_slots.py v34_width_joint_NOT_SUBMISSION.kmb v34_joint_slots_NOT_SUBMISSION.kmb

Literature: DeCross et al. qubit reuse (causal cones and mid-circuit reset); Hua et al. CaQR (circuit adaptive reuse); Rovara et al. qubit reuse/rewiring and Fang et al. scheduling (related dependency and allocation decisions); Faro et al. reversible lifetime semantics (abstract only). Implemented our own BDD and version-aware scheduling, not their CP-SAT/ILP or type system. Lean checks generic interval overlap, carry collision and phase identities, not the full native circuit or BDD extraction. No official verifier run, no full36Q, no main/Kaggle mutation.
