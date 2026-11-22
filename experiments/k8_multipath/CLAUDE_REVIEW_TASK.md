# GVQCC k8 — Claude independent implementation assignment (2026-11-23)

**Goal:** Produce a **new executable KMB** with fewer than 211 CCX/Toffoli for `angle_k_8`; do not claim a score increase from free CX reductions.

## Public baseline
- V8 Kaggle source: https://www.kaggle.com/code/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders
- Exact public k8: SHA256 `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`, 128Q, 211 T, 82 scratch products and 129 output products.
- Previous k8: SHA256 `cb689cf38c0c820a776b9ff8cac5eee4564f8359c5cd907d6db7e6bf3937ef99`, 128Q, 213 T, 82 scratch + 131 output.
- This branch has `get_public_211.py` and a successful SHA-pinned download run: https://github.com/corcondor/gvqcc/actions/runs/45047992163

## Evidence that determines search priority
We evaluated every CCX control product on all 1219 reachable addresses. Comparing old 213T and public 211T: of 82 scratch products, 74 are identical and the **last eight** were changed. None of the output-side product Boolean functions are shared between the two implementations; output multiplications fell 131 -> 129.

This does not prove causality, but strongly prioritizes **joint selection of the 8 high-cache AND functions and complete tail tensor resynthesis**, instead of isolated CCX deletion.

Fixed-cache output-only search was negative: 5->4 among 3439 valid five-fanout relations: 0; 6->5 among 28809 independent rank-5 fanout sextets: 0. These are narrow negative results, NOT lower bounds for all circuits.

We produced 7 score-neutral, SHA-distinct alternate KMBs (adjacent-CX, commuting-CX, 3 single exact cache-control rebases, combined rebase, combined+CX). Each retains 211 T and passes all 1219 addresses, both forward and reverse, scratch=0 and HMR symbolic phase checks; note this is not the native official verifier. Their accompanying ZIP is available from the assistant's conversation.

## Independent Claude tasks
1. Rebuild a cost-aware high cache / matroid parity / FWHT candidate compiler, changing **the cache product set and tail simultaneously**. Make the output a KMB, not a tensor proxy.
2. Independently search alternative nonlinear primitives or cache-lifetime schedules within the 128Q width, retaining measurement phase corrections.
3. Optionally explore equivalent integer angle tables with the high-bit cache/tag constraints, but require actual KMB construction and chemical numerical checks.

## Acceptance / handback
- Provide changed circuit `k8_candidate.kmb` and SHA-256, exact T/CX/HMR/Q, code with deterministic reproduction commands.
- Verify all 1219 legal address rows in BOTH directions, all 35 word state bits, scratch return to zero, all measurement-conditioned phase coefficients.
- If possible, also run unchanged competition Kickmix and chemistry official verifier on a complete 15-bank family; report source input SHA.
- No Kaggle submission unless user separately requests it. No token/key/paid model setup hidden in repository. Preserve original authorship and NOTICE.
- If no 210T result, report the exact unsuccessful search domain and tested code; do not present a proposal as a verified gain.

Please work on a separate branch or attach a patch; do not overwrite the baseline.
