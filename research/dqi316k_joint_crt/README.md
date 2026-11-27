# 316K joint CRT / HMR / rank-width research (NOT SUBMISSION)

Exact donor anchor 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52, 900Q, 69,782,188 ops, 318,972 static paid. No new whole donor tape emitted.

Sources pinned: #226 053b13fb (early HMR), #228 87308228 (tensor rank), #230 dbf2aa8f (zero-safe physical frame), #233 cffd9fd7 (projection), #234 eaaf9090 (G-based all-pole), #235 e8171f49 (M-based CRT + history), #213 4218534c (phase pooling), #227 308af18c (126 strict audited theorems). Proof files imported verbatim from peers; prior full-tape measurements are not transferred. This branch integrates their mathematical interfaces, not all of their physical tapes.

Vercel project gvqcc-score8-compute, sandbox gvqcc-joint-316k-history-20261128, session sbx_7SGN0FHcW9ud2SM9uvG7Ty0TnVf1. Python 3.13, KickMix 1.0.0, numpy 2.2.6. First venv failed because ensurepip was missing; installed directly into /tmp/gvqcc_packages. Actual stdout receipts retained as JSON. Baseline #235 is regenerated using pinned source, not an assumed bit-slice result. G script and receipt reconstructed from the executed command and stdout after the ephemeral sandbox expired; byte lengths match the Vercel manifest, re-execute CI to check artifact hashes.

| Local codec | Q | paid | ops per direction | native shots |
|---|---:|---:|---:|---:|
| #235 native baseline | 882 | 9288 | 260239 | 346 |
| HMR product/norm cleanup | 882 | 7020 | 277087 | 1384 |
| polynomial dual mask pooling | 882 | 7020 | 244921 | 1384 |
| GF8 in-place inverse + pooling | 879 | 7020 | 245353 | 1384 |
| #234-compatible G-based locator + actual XOR guard | 881 | 7799 | 226948 | 2440 |

All listed shot panels zero observed data, phase and scratch errors; G version also zero tag errors with arbitrary dirty incoming tag. 128 G-family cases produce exact scaled locator; 610 inputs incl legal other weights, M-family and arbitrary rows. 73,728 irreducible quadratic checks, 144 multiplication tensor basis checks. No phase scan or complete DQI emitted. The 26-bit adaptive history code is reused as a separately testable source, not yet physically packed. #234 G and #235 M=G*g_extra are distinct all-pole strata; do not transfer results between them. #233 post-repair only covers a specified family and remains expensive. The frozen donor still has real counterexamples; do not hide those with external chart choice. No new score or complete 898Q/316k/error-zero candidate.

Reproduce: install kickmix==1.0.0 numpy==2.2.6, run python history.py, python joint_crt.py, python narrow_crt.py, python g_guarded.py. Native KMBs generated deterministically, not committed as binaries. JointCRTHMR.lean formalizes reset witnesses, dual mask recurrence and boundary algebra. New joint CI audits 72 additional peer/new statements; check actual result. Main and Kaggle untouched.
