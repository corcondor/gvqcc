# Full 75-bank dual tensor ANGLE synthesis — research only, NOT SUBMISSION

Integration: #19 sign gauge, #20 strict independent XOR contract, #148 stationary transport, #149 weighted syndrome projection. Prior reports were read; there is no live cross-session execution.

| Family | loader width | CCX/pass | all legal address, arbitrary-target and HMR checks |
|---|---:|---:|---|
| previous narrow reference | 34 | 23622 | pass |
| independent affine tags | 34 | 23619 | pass |
| shared dual tensor | 34 | 22789 | pass |
| shared dual tensor | 35 | 22189 | pass |
| high-address tag joint search | 35 | 22233 | pass, rejected |

35Q: 17334 → 15589 mixed tensor operations; 670598 serialized ops; 6600 HMR. Re-read all 75 serialized KMBs by SHA256 and verified all 1219 legal addresses, arbitrary initial target XOR (symbolic coefficient tracking), all HMR phase coefficients, selection and scratch restoration. Weight-only retrain: 245 evaluations, 24 accepted, same angle table and tree. e1=0.019925994069611753 Ha, e2=0.019999980001472715 Ha, Lambda=283.0699956518514, E_gap=3.914898005001305, lambda_eff=46.91539082344683. Very narrow physical slack. Cost model: full chemical Q=377, T=50878, local cost=899884392.8768785 vs prior narrow 950595613.1220548. Conditional total score=21.675232656399 (NOT a leaderboard result). Reference 3357 CCX/pass, 128Q loader, 405Q full chemistry, cost approximately 251089996, conditional score 33.17031. NOT competitive; no official verifier, submission, or main mutation.

The attached conversation archive GVQCC_Chemistry_GlobalDualTensor_35Q_NOT_SUBMISSION.zip (423 entries, SHA256 84c2e2f76194592906a330efb1ade1156400ba5bdaba3ff345f562ecd939be6b) contains the full exact emitter, all 375 KMBs across five families, weights, previous input, packed reference, receipts, logs, and a recheck script. Extract and run from chem_global: OPENBLAS_NUM_THREADS=2 python recheck_final.py. Full regeneration commands in archive README_JA.md. This branch includes the standalone shared tensor kernel with its conventional rank routine inlined, local Lean identities, and measured receipt. It does not store the large binary archive. Lean CI is not yet confirmed. No claim of formal verification of the full KMB.

Method: choose dual constraints in the exact row annihilator, construct paired rank-one features sharing one output direction, and verify coverage/reconstruction before reversible emission. Keep every loader's scratch clean; no cross-bank live scratch. See Gidney https://arxiv.org/abs/1709.06648 (temporary AND); Low/Kliuchnikov/Schaeffer https://arxiv.org/abs/1812.00954 (width/cost tradeoff); Shende/Bullock/Markov https://arxiv.org/abs/quant-ph/0406176 (state preparation/multiplexors). Hamada/Iwata, A Shortest Augmenting Path Algorithm for Linear Matroid Parity, motivates paired dictionary search; we do not implement their exact algorithm or claim global optimality.
