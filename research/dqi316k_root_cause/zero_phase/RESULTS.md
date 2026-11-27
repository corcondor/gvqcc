# Native 316k zero-syndrome phase partial repair — NOT SUBMISSION

Parent recovered from user's saved candidate_900q_dqi_only.zip: SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52. Native candidate rebuilt byte-identically, SHA256 1ea5587d8a9b6ddda55429956d2770d401bb856e789034d4f9f7b521d05b58a9. Parent provenance: Tony Li/tonylica public task-generator dataset and PRs #208/#209/#227. Preserve attribution. No external chart selection or syndrome measurement. The classical shadow specializes the parent at zero quantum input using only mask and original measurement outcomes. On the restored legal domain, the first 35 moments being zero implies weight zero by the existing Vandermonde certificate (35+w at w=0). The quantum guard applies the shadow phase debt. HMR with outcome-conditioned CZ uncomputes AND intermediates using existing ancillas. The method assumes zero-input syndrome/workspace restoration; does not repair corrupted nonzero outputs. Independent rules/architecture review and full physical proof remain open.

| metric | parent | candidate |
| --- | ---: | ---: |
| qubits | 900 | 900 |
| static paid | 318972 | 319770 |
| operations | 69782188 | 110708810 |
| mean paid, matched ordinary distribution 1024 | 316122.396484375 | 316530.748046875 |
| zero-weight phase errors, combined 144 | 81 | 0 |
| weight 1..17 value errors, combined 336 | 336 | 336 |
| weight 18..35 errors, combined 352 | 0 | 0 |
| ordinary distribution errors, 1024 | 0 | 0 |

Extra static paid successive implementations 3290 -> 1618 -> 798. Native KickMix 1.0.0; no unchanged official verifier, reaction depth, official score, whole-circuit Lean proof, or Kaggle submission. This is a partial phase correction and costs +408.3515625 mean paid on the matched ordinary panel; no cost gain claimed. Parent remains unrepaired on weights 1..17. Do not submit. Priority: fix coherent low-weight extraction, phase and cost.

Reproduce: verify exact parent SHA; compile g++ -O3 -std=c++17 zero_phase_repair.cpp -o zero_phase_repair; run ./zero_phase_repair parent.kmb candidate_35.kmb; verify candidate SHA; run PYTHONPATH=/path/to/verifier python extended_test.py parent.kmb parent.json and same for candidate. Extended panel: 576 forced (16 per weight 0..35), plus 1024 distribution. Extended alone: zero 10/16 -> 0/16; low 272/272 unchanged; high 0/288 unchanged. Additional 256-shot native panel and both full receipts are included with the binary research archive. No parent bytes committed.
