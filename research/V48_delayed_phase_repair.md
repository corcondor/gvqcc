# V48 — delayed phase repair of the nonmonotone V47 route

Research artifact, NOT a completed 36Q submission. Parent: PR #106 V43 phase frame, SHA-256 1dceb7979691172971b9f87bab5e7b9d34342e24bf84acd995b5f5ae0aecb1e8.

- V47 three-product route: physical width 36 but unresolved measurement-558 phase debt.
- V48: expand the observation dictionary to 40 frames (12 body, 28 later source), test 33,350 constant/linear/quadratic atoms using 4,732 sampled legal inputs, then check all 20 nonzero coefficients over all 3,133,452 legal inputs exactly. The first fit passes; record 556 requires no correction.
- Delayed 558 repair: 23 phase operations, including 7 observations at source cuts 10384..10425. No new nonlinear gate for the phase repair. Preserve the original HMR events, with no presampling or postselection.
- Extended source interval [10152,10425): 273 source ops, 12 paid. Repaired 3118 ops; affine compaction 498 ops, 13 paid, physical 36 wires.
- Independently re-read the fragment and full hybrid KMB; changed-window data, rotations, classical records, guard/stack and phase ledger all PASS. The full hybrid retains an identical prefix and suffix; 1,280 HMR variables. Expected paid count 23159/16=1447.4375; 41,812 ops; full-occupancy cuts 2817 versus parent 2819; whole width still 37.
- Fragment SHA-256 11546137241d6dc563b7a601c3f478006eff7cd9980b9b1bd97f99ae1bfcc1a8.
- Hybrid SHA-256 2043c15796987eb15546eba25af8fe219c649efa912ca9a09a00ea1b651ff0e1.
- V46 peer already reaches the same occupancy and expected paid count via a shorter presampled-HMR replacement. V48 is a different validated phase-repair route, NOT an improvement over that peer in the aggregate. Do not add the two overlapping replacements.
- The Fourier manuscript in corcondor/math motivates prediction plus exact residual repair; its full spectral-repair algorithm is not implemented here.
- Reproduce from the companion V48 archive's repair directory: python v48_delayed.py; python v48_compact.py. BDD verification, not a full Lean proof; official verifier not run. No main-branch merge or Kaggle submission.
