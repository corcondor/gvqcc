# V56 multilevel carry and prefix sharing — research only

Not a submission. Parent: PR128 dictionary34, SHA256 63b11abe5df0e59a01c0ddce2020d1b5f93656106518125e26e03339996ebd12; PR130 tensor/one-level carry comparators.

| Native circuit | Q | CCX | Generic rotations | Ops | HMR |
|---|---:|---:|---:|---:|---:|
| tensor + prefix |36|16379|5389|169701|5390|
| carry + prefix |36|19089|4348|208175|6431|
| persistent multilevel |36|25290|3975|283864|6700|
| multilevel recluster |36|23019|3926|281114|6616|

All four were serialized, independently reread, and checked over the full 22-bit cube for control values, every independent HMR phase coefficient, restoration, and exact modular phase; 3,133,452 legal inputs satisfy the integer squared tolerance. Worst observed error/tolerance ratio 0.8125815968960524. This is a construction-specific check, not the official competition verifier.

18,003 local terms -> 11,907 with 5,385 triple carries, 292 identical predicate carries, maximum depth ten. Only four triple transformations include previously nonlinear predicates; no claim of unrestricted nonlinear closure. Shared prefix saves 2,524 CCX on both original V55 circuits. An initial prefix candidate failed verification because future leaf slots were reused as clean scratch, then the clean set was fixed. The rejected KMB is excluded.

Reclustered native SHA256: dee92da7e917587f8409798c22c7e243edc7ae894db318112939948f9d5489fd.
Tensor-prefix native SHA256: d76ac1029960ac38f383891cd2175b5ce0742f010c2469bc59ce53bc36a80421.
Carry-prefix native SHA256: 9328473779036ed739f4e4c6caa0e866706ee0805a59391a1a5d508f6a5a6084.
Persistent native SHA256: dfd92311f8e794c5628370202f0dcc19e47bb688ce4b52d964c24a6ce25ff5bb.

The complete compiler, parent and generated KMBs, plans, receipts, logs, and reproduction instructions are in the V56 research archive delivered separately. This branch adds local Lean identities and an associated workflow, not a full Lean proof of native circuits. 

This applies finite shared tensor organization, Boolean carry factoring, and exact phase bookkeeping. It is not an implementation of OpenAI's asymptotic FFT or matrix multiplication results. Even ignoring rotations the lowest CCX candidate costs at least 589644 qubit-Toffoli units. No competitive improvement, official score, submission, or main-branch change. PR132's truncated-product arithmetic rather than full-spectrum dictionary expansion remains the cost-critical route.
