# 2026-11-23 | Reversible state feedback / ancilla cost experiment

**Result: no new official or Kaggle score**. Published public leaderboard benchmark = 33.17023 (Mizero Lucky Gall V8); published local three-task cost baseline from that notebook computes to 33.170276600087455. These must not be conflated.

## Executed (original local reproducible bundle)

- 13 new small KMB-v2 versions (T-flop, reversible CSWAP D latch, 1-CCX MUX, 1-CCX conditional parity, dirty-output shared AND, clean cached AND, 4-bit LFSR, ternary ABC modulo adder and CSA). 2 additional ancilla-budget schedules.
- 11/11 Python unittest groups PASS, including all 4,096 A/B/C 4-bit inputs per arithmetic scheme and clean-return tests. All 13 emitted KMB gate streams re-read and matched the intended operations.
- Same-function comparisons (strictly local, not full KMB): 2->1 CCX for four-wire conditional MUX (0 extra Q); 3->1 for three-way XOR-controlled update (0 extra Q); 4->1 for four-target same-AND fanout (0 extra Q); the CSWAP latch uses the same Toffoli-equivalent as its 1-CCX/2-CX decomposition.
- Reqomp-style reversible pebbling on the four-input AND chain: 3 clean/6 CCX versus 2 clean/8 CCX, both with all scratch restored.
- Public DQI full 900Q SHA256 `4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52`: 69,782,188 operations and 311,858 explicit CCX. Commutation-aware paired-CCX scan up to 2048 operations found **0 certified savings** among 216,486 proximity-only witnesses. No invented T gain.
- Public 37Q inverse-sqrt three-T-edited SHA256 `bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`: 60,766 operations, 1,468 explicit CCX and 42 CSWAP.
- Across 15 older V8 ANGLE KMBs, all 861 candidate two-CCX / small affine windows (<=8 wires) were tested for a necessary 1-CCX algebraic rank property; **0 eligible**. These older 3375T loaders must **not** be treated as the current 3357T frontier.

## Real whole-invsqrt KMB rewrite (verified phase identity, NO improvement)

Actually emitted an entire edited 37Q KMB converting all **42** unconditional CSWAP to CX-CCX-CX. Verified all 8 local basis states per gate and preserved every other operation stream, angles, classical records, and registers:

| Metric | Original | Rewritten |
|---|---:|---:|
| 37Q operation count | 60766 | 60850 |
| CCX | 1468 | 1510 |
| CSWAP | 42 | 0 |
| CX | 29972 | 30056 |
| CCX+CSWAP (same cost) | **1510** | **1510** |
| Q | 37 | 37 |

New KMB SHA-256 `810f84ca9dd815b262456ee199c096f001de5e8ab9f33cef74e034fd1c1b24d1`. This change is rejected numerically: zero native cost improvement. Complete original source notice retained in the local package. No official verifier was run.

## Numerical decision under unchanged task conditions (NOT an official score)

From the public notebook's task costs: invsqrt 60927.5767, DQI 305041647011.3978, chemistry 251090780.94. The baseline three-task formula yields 33.170276600087455, while the actual public badge is 33.17023.

| What-if, requiring a fully legal implementation | Conditional score delta |
|---|---:|
| invsqrt 37Q, save 1 average T-equivalent | +0.00671725 |
| DQI 900Q, save 1 CCX **per shot**, unchanged R | +0.00003498 |
| chemistry, save 1 CCX **per loader pass** (two passes), unchanged Q and lambda | +0.00167366 |
| invsqrt 37Q→36Q, gain 1 global clean wire, +2 average T | +0.29079016 |
| DQI 900Q→899Q, +2 mean CCX, unchanged R | +0.02452335 |
| invsqrt 37Q→38Q, save 2 average T | **−0.28023667** |

Width savings are unachieved thought experiments, NOT claims that 36Q invsqrt or 899Q DQI is legal. All 900 DQI qubits are touched; removing an unused wire cannot reduce width. If adding a new clean cache actually increases global Q, a 2-CCX local saving can make score much worse.

## Reproducibility and scope

The ongoing conversation contains a ZIP with source, full local 37Q rewrite, 13 original KMBs, unit tests, CSV/SQLite experiment registry, SHA ledger, score formula, real-circuit scans, and provenance. The established GitHub PR17 has the earlier reversible arithmetic and pebble code; this update adds independently tested D/T latch, parity, MUX, and LFSR synthesis source + tests.

References:
- https://www.kaggle.com/code/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders
- https://github.com/quantumlib/Qualtran (Apache-2.0)
- https://github.com/eth-sri/Reqomp (MIT)
- https://arxiv.org/abs/quant-ph/0410184 (Cuccaro)
- https://arxiv.org/abs/1709.06648 (Gidney)

**Status: 0 certified global KMB savings, no native KickMix runs, no official score.** Main untouched.
