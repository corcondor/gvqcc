# V130 — 897Q full native phase-pooling integration (NOT SUBMISSION)

Parent: PR #214, exact archived binary SHA256 e270bb38fc389e42605bc821846498517af7db1e33d19d01570fdf414414ff01, independently read back with KickMix 1.0.0: 897Q, 51,481,680 native instructions, 475,065 static paid.

Transferred the proven V129/#213 phase-mask pooling pass to this exact parent. Candidate SHA256 1521ab2d84dd7257be56785c9c7a8b12ffe3f3574ecb4d1b47f7014ff9eca5e2, 897Q, 51,162,831 instructions, 475,065 static paid (unchanged), 2,125 changed regions and 19,169 pooled masks. Local expanded-XOR coefficient checks all passed. New independent complete-circuit checks: 4,096 distribution + 256 forced-weight/position-52 + 1,728 saved matched cases, all 6,080 zero value/phase/workspace errors, mean paid 414984.93701171875 on 4,096 ordinary shots. Reaction depth omitted; not unmodified official verifier results. No Kaggle submission or universal decoder guarantee.

New two-step scalar-frame formula (JointGauge.lean) and independent classical GF(2^24) check: 32,768 coordinate cases and 98,304 phase identities, no errors. This is an algebraic identity; not a new implemented full replay optimization. Strict Lean CI is required before calling the six new theorems formally verified.

The 898Q #215 adaptive-ladder transfer is a separate source-level experiment at cap 897, not included in this candidate. Exact source/replay archive supplied separately. Main untouched.