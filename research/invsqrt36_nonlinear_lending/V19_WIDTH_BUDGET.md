# V19 source recovery and exact q36 lifetime attribution

Research only, no new optimization search or score update. Actual PR68 archive manifest matched, prefix replay passed, independently replayed all 3,133,452 legal inputs / 1,280 independent potential HMR variables. Native SHA bf041c7baea460594002045116a028069dd28e56fc988987bc65caf36c1d6ad2. This replay checks exact expected cost and terminal data/scratch, not fresh full oracle phase; the separately rerun prefix boundary and identical verified suffix establish compositional equivalence.

306 maximal q36 non-identically-zero lifetimes, 2,024 direct touches; 13,126 native ops in lifetimes, expected 431.875 inside, 979.4375 outside, 152.5 directly touching q36. 83 swap-only, 108 swap/Clifford-phase only inclusive of those 83; 171 have zero direct paid cost. Every lifetime has at least one cut with all 37 individual wire functions non-identically zero. This is NOT a joint nonzero witness or an information-theoretic lower bound. No new synthesis.

Frozen score model: Q36 requires additional expected cost <40.74140236 over PR68, assuming unchanged rotation and other components. If sixteenth grid remains valid, budget <=651/16. At most 81 lifetimes can add >=0.5 expected each in absence of compensating savings. Not a general width or lower bound. PR69's distinct exact phase-rank audit should be used jointly, not double counted.

The four missing ANGLE experiments have pinned SHA256 and existing reports; no archive recovered from previous conversations, relevant library/Drive folders, repository trees/comments or five successor archive member lists. Generic Actions artifact listing endpoint denied, not proof of absence. Keep ANGLE baseline 3357T/128Q and discovery stopped. To recover, publish original files or SHA-pinned complete source and receipts; no main changes. Separate invsqrt track requires its own complete novelty audit before launching new discovery; missing ANGLE sources are not an invsqrt impossibility result.

Reproduce using V19 companion archive: verify SHA256SUMS, run python prefix_reuse.py, python v19_width_budget.py. Exact per-lifetime receipt and source included in companion archive, not a submission. Lean file only certifies arithmetic statements, not the full BDD trace.

References for future design:
- https://doi.org/10.22331/q-2025-02-18-1636 (spooky pebbling, measurement-aware memory).
- https://lmcs.episciences.org/17091 (classical/quantum space trade-offs).
- https://arxiv.org/abs/2610.41142 (encoded reversible arithmetic).
- https://arxiv.org/abs/2611.02345 (automated measurement-based uncomputation).
These are design leads, not implementations or novelty claims.
