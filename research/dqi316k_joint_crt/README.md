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


## Full phase scan integration, Vercel follow-up

The preceding joint strict CI run 46071109254 succeeded in both Lean and native-local jobs (72 additional theorem audits, plus prior 126 in run 46071109257). Reuse G-based codec; new nested-norm phase scan moves the fixed G(x)^-1 to the classical mask, attaches the chart/root bit to the innermost 3-bit inverse, and clears each measured field product by the exact witness phase. Rolling Chien evaluation of all 4095 nonzero x uses x*D'(x) as the odd-power sum in characteristic two. A GF(4) five-point degree-4 interpolation gives an explicit 15-product GF(64) tensor; all 36 binary basis pairs verified. The group AND ladder reuses the leading coefficient flag and reduces scratch by one.

Actual Vercel KickMix 1.0.0 results, session sbx_qSEPkCU0HfXHa13WnWc5OzAM3nOG:

| guard + codec + phase + inverse | Q | paid | instructions | native shots |
|---|---:|---:|---:|---:|
| #234 prior chart-only oracle |898|268650|25206956|1718|
| joint_phase.py |881|236728|17817019|144|
| joint_rank15.py |880|223579|17917828|432|
| rank15 with public register ABI |880|223579|17917828|432|

New oracle identity on the chart complement; all listed new shots have zero syndrome, mask, workspace, and phase errors relative to that chart-only contract. Public ABI check: exactly 70 quantum S registers and 4095 classical E registers of width 12, physical q0..839 and b0..49139. Final KMB SHA-256 f99e60190524fe0121ee5216d4a94195d49cfd31d9f6fe5eeaf06faa81e1bccc, 4165 registers. Original pre-ABI receipt retained. No official distribution verifier PASS claimed: complement deliberately identity, so cannot submit alone.

Independent local KickMix replay of exact donor SHA-256 4b572141... on the same 96 legal G-all-pole inputs, same masks, 2 seeds (192 shots): 192 value errors, 96 raw phase errors, zero mask/dirty errors, union 192, mean paid 305073.6145833333. New chart-only oracle zero all errors on these inputs. This is a matched specialized stratum, not the full DQI score or an integrated donor replacement. Compare script uses same generator as Vercel code; independent measured donor receipt retained.

Lean GuardedPhase316.lean adds exact finite rank-15 basis certificate and algebraic composition identities. Verify strict CI separately; no physical tape refinement proof asserted. Existing proof files retained. Reproduce with Python 3.13, kickmix==1.0.0 and numpy==2.2.6: python joint_rank15.py --count 4095 --cases 96.

Remaining: the 901Q #236 full tape and complete generator not acquired from peer archive; full integration must use a reversible branch dispatch or a proved physical seam, not host selection or measured syndrome. Low/high/complement defects still unresolved. Do not merge or submit.


## Saved-panel independent replay
Retrieved exact CI artifact 15233053080; the serialized public-ABI KMB hash matches Vercel. Public verifier validate_registers passes. Local KickMix 1.0.0 replay on original saved hybrid_cases.npz (SHA-256 ea5e22c1...): all 20 G-allpole rows 602..621, both seeds. Donor: 40/40 value failures, 26 raw phase failures, mean paid 316176.8. New 880Q chart-only oracle: 0/40 failures, paid 223579; all 1244 shots across all 622 rows have zero errors against the chart-only contract (identity complement). Original mask words retained. Not evidence of repair of the complement or #236's full circuit. See saved_panel_receipt.json.

Initial GuardedPhase316 strict CI 46072220081 elaborated all 12 theorem proofs with no prohibited axioms but rejected two linter diagnostics (deprecated if_true and unused Bool.true_eq). Fixed in cafa0c4 using ite_true, without weakening the statement. Re-run 46072526234; inspect actual conclusion.
