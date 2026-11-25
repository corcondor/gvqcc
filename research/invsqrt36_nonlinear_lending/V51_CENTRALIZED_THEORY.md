# V51 — 36Q centralization research hub / 共同研究ハンドオフ

**Research only / NOT SUBMISSION.** Target is a competitive *complete* invsqrt oracle, not merely a 36-slot fragment or a circuit with thousands of arbitrary rotations. This branch forks PR #116; PR #114's 37Q budget frontier remains a distinct donor, not an additive improvement.

## Measured results (2026-11-25 JST)

| Circuit | Physical Q | Static CCX | Generic rotations | Native ops | Status |
|---|---:|---:|---:|---:|---|
| PR116 shared-prefix analytic diagnostic | 36 | 274 | 18,787 | 81,891 | approximate target |
| V51 sibling transport + persistent parity gauge | 36 | 160 | 18,787 | 50,157 | same phase as PR116 diagnostic |
| V51 adaptive spectral selection, 80% analytic error allowance | 36 | 160 | 15,280 | 41,002 | different approximate target |
| V51 adaptive spectral selection, 100% allowance | 36 | 160 | 14,553 | 39,099 | near zero synthesis margin; diagnostic |
| PR92 archived exact source (cf1ba95...) | 37 | 1,489 | 33 | 51,317 | pinned source |
| V51 physical sparse-control repair of PR116 spec on PR92 source | 37 | 45,297 | 32 | 107,384 | expensive existence diagnostic, **reject for score** |

The first V51 36Q oracle preserves the exact multiset of 18,787 control-mask/angle tags from PR116. CX 62,546 -> 31,041, CCX 274 -> 160. Serialized replay of every control mask on all 2^22 computational basis states, register restoration, global parity cancellation, and exact integer squared tolerance on 3,133,452 legal inputs all passed. SHA f2a120539a084595385f3b8df2faef6b25b6d6e9979085a73f593c12f7446f86. Source diagnostic SHA 8ea5a6a816eafd7a779052c7efa79b16f8683754cf8b3964acbd5bba00d2977b. No official verifier or rotation-synthesis error assessment.

Adaptive integer Walsh support/quantization uses actual finite block transforms; exact acceptance, not an asymptotic FFT. 16,520 -> 13,453 terms at 80% allowance; 15,280 native generic rotations, worst relative error ratio ~0.7998046875. SHA 57316aacce41f47eca1c023dee1456b83091dd21d182f5ae14acad447df42b45. At 100%, 12,825 terms and 14,553 rotations, worst ratio rounds to 1.0; exact squared test passes but reserve is negligible. SHA 4d0322c364e0df6f8f4f9a0d589b61244d5e67ecb35c32d8859c151b2bc3e735. Distinguish exact PR92 phase from approximate analytic target.

## New physical 32-rotation repair (negative economic result)

PR116 had a 32-generic-rotation **specification** only. Re-extracted PR92 phase from archived ANF: all eight assignments of its residual three history variables give the same phase on all 3,133,452 legal inputs. Six target-free stable frames, one dropped root (3). Initially 192 errors. Fiber audit identified 7 ambiguous exceptional inputs at root17 and 1 at root36; reselected toggle combinations to avoid ambiguous fibers. All 192 repaired, 288 total control flips. Each singleton is an exact legal-domain cube of existing frame coordinates; no q36 used for repair. Grouped dirty-toggle detection with shared common factors: forward correction 25,976 -> 21,904 CCX, 55 selected groups; conjugation doubles that. Six serialized correction fragments independently verified on every legal input, exact data restoration and expected control toggles. Source HMR sequence unchanged (1,276). Recomputed integer phase tolerance PASS, but whole parent is still 37Q and 45,297 CCX. SHA 1da9597545568d91ef26ebbfa9eef7e4ea7d8e871e60d4d95489fb1d5832da65. **Do not treat this as a competitive candidate**. It identifies the remaining task: economical care-set predicate generation and transport, not existence of a physical 32-rotation circuit.

## Shared theory

See [ROADMAP_V51.md](ROADMAP_V51.md), [tasks_v51.json](tasks_v51.json), and [Lean identities](lean/V51CentralizedTheory.lean). The four names are proposed research directions, not claims of new established mathematical fields. Local Boolean identities are established; global synthesis, general new theorem novelty, full Lean circuit equivalence, competitive 36Q and official score are open.

Companion reproduction archive: GVQCC_V51_CentralizedTheory_NOT_SUBMISSION.zip (ChatGPT Library / research conversation). Contains pinned PR116 archive, actual emitted native KMBs, scripts, exact-check receipts and commands. GitHub core includes the portable emitter transform and quantization search. No main merge or Kaggle mutation.
