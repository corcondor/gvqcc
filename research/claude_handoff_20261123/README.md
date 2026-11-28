# GVQCC 2026-11-23 — Claude collaboration handoff (active research, NOT VERIFIED)

**Goal:** Beat the *officially verified* combined score 33.13521306472748; also benchmark against publicly reported 33.17023. Do NOT claim a new record without official KickMix full verification. This is a public research branch for external collaborators.

## Actual experimental artifacts (available as ChatGPT conversation attachments; source is being published under `research/claude_handoff_20261123/`)

- Global angle-gauge / joint FeMoCo study: `GVQCC_20261123_GLOBAL_ANGLE_GAUGE_JOINT_PHYSICS_REAL_KMBS_RESEARCH_UNVERIFIED.zip`.
- C45+B130 angle/W/H2 exploration: `GVQCC_20261123_C45B130_Nonlocal_Angle_W_H2_45KMB_RESEARCH_UNVERIFIED.zip`.
- Nonlocal invsqrt phase proof + altered 18-file ZIP: `GVQCC_20261123_nonlocal_invsqrt_9T_original_phase_proof_RESEARCH.zip`, `GVQCC_33p135_nonlocal_invsqrt_9T_UNVERIFIED_20261123.zip`.
- Structural patterns A/B/C/D: `GVQCC_20261123_multiple_structural_patterns_EXECUTED_NO_OFFICIAL_RECORD.zip`.

These archives are **not independently hosted on GitHub by merely naming them here**. Request the ZIPs from the project owner if missing. This branch will contain extracted executable source, reports and a handoff.


## CRITICAL RESEARCH RETRACTION (2026-11-23): 9T invsqrt rewrite is UNSAFE

A later branch-aware HMR check found a counterexample to the previously claimed exhaustive phase equivalence for `invsqrt_nonlocal_9T`. The original T triples at ops 32662/32663/32665 and 34341/34342/34344 are under classical condition b743; the replacement S insertions at ops 8145/8344 are unconditional. The previous test ignored this scope. Branch 0 has 1,300,770 phase mismatches and branch 1 has 749,964; **x=0 is a witness**. This 9T candidate must NOT be submitted, scored, or handed off as valid. Full details in `GVQCC_20261123_temporal_products_DQI_liveness_BRANCH_PHASE_COUNTEREXAMPLE_RESEARCH_NOT_OFFICIAL.zip` (research archive). The older public 3T→2S control passes the tested 2 global HMR branches but is not an independent score gain. The files mentioned above are historical negative controls. No valid 9T score improvement is established.

## Evidence and failures (from the included study's README / scorecard)

- Baseline: public C46 V8 ANGLE family, 15 KMB, 3357 CCX per one-way loader pass, 128Q (loader width). Combined score still UNVERIFIED for changed candidates.
- **I / affine sign-frame conjugation:** 33,673/91,425 angle words changed (55/75 columns); 15 modified KMB, 3357 CCX/pass, max 128Q; +292 CNOT and +18 X. Local phase/value/scratch PASS on valid sequential 1219-address trajectory. No CCX reduction, not a score update. Arbitrary dirty-word inputs fail even on the original loader; do not generalize the normal-path proof.
- **J / C45+B130 / W/H2 orthogonal gauge / angle-gauge:** 30,976 angle words changed; 15 KMB, 4429 CCX/pass, 127Q loader; model lambda_eff 48.834963 vs 48.836154. Model + local checks only. No demonstrated improvement in overall official cost.
- **G / full-tree angle fold:** 52,591 words changed, full KMB family 4615T, max 126Q; physically equivalent state vector on the tested model, but substantially more CCX than the baseline.
- **H:** dynamic-programming gauge ranks improve from 7175 to 6221, but compiled first five banks are 1592T vs 1136T baseline. Therefore **ANF rank is NOT the cost objective**.
- **S6:** 70 rank constraints leave 4 free sign variables per address; 22 tested families, best checked first three banks 859T vs 840T from the same compiler.
- **A+B:** 122,486 CNOT removed vs original 481,724, but CCX and Q unchanged. No score benefit by itself.
- **C:** changed AND basis with **zero** net CCX savings. Single-product deletion in existing loaders was negative in prior research; do not retry identical local fusion as a primary strategy.
- **D+F+G ROM variants:** 61,080 -> 36,210 -> 18,105 -> 9,003 ROM CCX, still worse than 3357 baseline. ROM width 56–118Q depending on approach. Note the 18,105 variant uses HMR-based measured uncomputation; phase checks are LOCAL.
- 900Q DQI naive first/last-use live intervals overlap across all 900 qubits. This does NOT rule out nonlocal schedule rewrites, rematerialization or HMR resets.
- 37Q invsqrt nonlocal phase rewrite: the attempted nine-T/four-S edit was falsified by phase-condition branch analysis; **unsafe, do not reuse**, despite earlier unconditioned tests.

## Implementation request for Claude

1. Work directly on the attached Python source and exact KMB/NPZ; avoid speculative score tables.
2. Optimize **(75 angle words + FeMoCo continuous parameters + 15 transition circuits)** jointly. The output of every iteration must be actual compiled 15-bank KMB cost, physical two-body/one-body errors, lambda_eff, Q, CCX, HMR-phase proof.
3. Explore 4 sign freedoms per address within the exactly maintained bank-coupling constraints using beam/search, genetic proposals, annealed exploration, and per-bank compiled *cost feedback*, NOT ANF-rank-only optimization.
4. Try new nonlinear basis with sharing/retention across consecutive loader transitions. Allow transitions to be compiled jointly if the official calling contract permits.
5. In parallel, evaluate C45/R/B/C/J physical-space alternatives and the actual score formula, DQI nonlocal scheduling, and 37->36Q invsqrt re-materialization.
6. Build official verification in CI if legal and executable. Test all fixed counterexamples plus official full panels, work wires, phase, physical constraints. No false score claims.
7. Save executable source, changed NPZ + KMB, exact SHA256, all negative attempts, raw scorecards, and reproducible environment commands.

## Mandatory integrity conditions

Never equate local arithmetic checks, model-error tests or proxy-gate estimates to official KickMix verification. Never claim negative results prove mathematical impossibility. Retain both target 33.13521306472748 and higher public benchmark 33.17023. Maintain SHA256 for each artifact. Report *specific KMB gate differences*, not descriptions of intended edits.

## Links

- Repository: https://github.com/corcondor/gvqcc
- Prior code on main: `chemistry_affine_span_resynthesis.py` and `chemistry_dontcare_v4_report.md`.
- Original study reproduction (relative to extracted ZIP): `bash REPRODUCE.sh` (requires NumPy; official KickMix verifier is NOT included).
