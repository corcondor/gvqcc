# V60 — shared Hamming-weight counts and phase audit (NOT SUBMISSION)

Parent: PR140 (V58). PR141–143 reviewed; PR139 multiplier estimates not treated as actual native implementations.

Native 36Q *partial* normalized two-stage phase, same target as PR140:
| variant | expected paid | generic rotations | ops |
|---|---:|---:|---:|
| V58 |1034|707|6185|
| V60 count, weight 0 or 2 |1332|564|9784|
| V60 count, weight 7 |1362|558|9790|

Compute coefficient-independent diagonal monomial counts n_k(t), then apply the shared retained coefficient W_k(a). Dynamic programming chooses singleton, half/full-adder or streaming counter groups. Actual native KMBs were emitted, re-read and re-verified over all 3,133,452 legal inputs, 1,041 independent HMR signs each, packed integer phase modulo 2^32 and input/scratch restoration PASS. Not a complete invsqrt oracle.
w0 SHA256 2487731c452586709ee6351c1d536b3e19b1947b12dcb5fd6b5878307afaaa5d
w7 SHA256 a6cc39eb542ec19c1fabd7a153ec2261ece3287e2e1f1c61a1bebe99ad254756
In illustrative E+lambda*R model, w7 at lambda=7 gives 5268 versus 5983. Not an official cost or score. 36Q incumbent budget 60927.56/36=1692.4322. w7 leaves only 330.4322 for 558 rotations and remaining stages; reject for submission.

Separate complete 37Q V35 cost-first parent: cross-support relation optimization removes 175 ops (55989 -> 55814), 33 of 387 selected groups accepted by exact proof, 1770 total candidate relations. Expected paid unchanged 22501/16, full occupancy cuts 4759 -> 4740. Serialized paired equivalence PASS all 3,133,452 legal inputs and 1276 independent HMR variables. SHA256 67215e86181ec85ba138e3d0c7fafac923d326c24c6234196620dba29ffd4c50. Temporal paid CCZ relocation: 2 sampled candidates rejected by exact BDD, no savings. Affine reset recheck: no savings.
Full compiler, inputs, KMBs, SHA256 manifest, replay scripts and logs: GVQCC_V60_SharedCount_PhaseAudit_NOT_SUBMISSION.zip, delivered in conversation, SHA256 98e95bf0ff59f385cbf957244c72127d4af6267440ece10e629976f08294ea7a.
References: Gidney, Quantum 2, 74 (2018), doi:10.22331/q-2018-06-18-74; Hamming-weight phasing, doi:10.1038/s41534-025-01091-0; Amy/Lunderville relational phase folding, POPL 2025. Finite adaptations, not full paper algorithm implementations. No new Lean machine check, official verifier, score or Kaggle submission. Main branch untouched.
