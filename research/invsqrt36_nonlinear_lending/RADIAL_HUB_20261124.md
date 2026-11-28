# Radial / central-hub representation search — 2026-11-24

This is **not a competitive invsqrt oracle** and **not an official score improvement**.

Reference: 37Q / 60,766-op invsqrt KMB SHA-256 `bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`.

New experiment: 171 program-wide q36-use checkpoints; 60 state identities (28 affine, 32 single-AND), all verified with reduced BDDs over 3,133,452 legal inputs and all independent HMR branches. Expanded source-state fitting at 304 cuts yielded 316 optimistic pivot-interval candidates (those 316 were sampled only, **not all certified**). Two emitted genuine **36Q INTERNAL KMB** macros pass independent full-BDD gatewise state / HMR sign / diagonal activation checks:

- Old ops [17656,17828), pivot q34: 172 old operations → 214 macro operations; +2 CCX, 1 HMR, 1 arbitrary-angle Z_POW; 5,880 BDD comparisons PASS.
- Old ops [17656,17795), pivot q31: 139 old operations → 181 macro operations; +2 CCX, 1 HMR, 1 arbitrary-angle Z_POW; 4,834 BDD comparisons PASS.

Original QROM/ANGLE fifteen-bank radial hub was already tested separately and did not beat **3,357T**, because each independently callable bank must construct and recover its own shared state. Do not count the same hub twice.

`RadialHub.lean` proves *generic* reversible pivot and X-basis measurement sign identities, **not** the specific all-input BDD witness, whole KickMix HMR instrument, 55 arbitrary rotations, or 36Q full program. Do not mark it as a completed DeepMind-style discovery or official verification.

The linked QAOA paper: https://arxiv.org/abs/2503.09356 . QAOA is evaluated as an **offline** QUBO solver for hub choices, NOT an available KickMix submission gate. For 12 real candidate choices, p=2 statevector simulation gives best-assignment probability 0.2799% (uniform=0.0244%), while exact enumeration over 4,096 assignments is preferable.

A nonunitary measurement/reset branch does not admit naive `U_j U_i^†` inverse. Whole-state routing must preserve the complete quantum instrument, random measurements, corrected phases, and independent bank ABI. Original scored circuits remain unchanged.
