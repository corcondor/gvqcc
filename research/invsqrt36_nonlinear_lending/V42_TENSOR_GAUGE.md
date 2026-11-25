# V42: finite-field tensor gauge and two-injection exchange
Research only, NOT SUBMISSION. PR101 parent track pinned to original V40 native SHA eaa9b9599ea36f3247aecd27d0105805b06835c39b7b26cdecd166453b976401. Independent PR103 native parent SHA 553f46ba954f4c306f4fbd1080342e2faffe1ef9ba800656e480b3d69ddec54e. No main or Kaggle mutation.

| Track | ops | E | all-37 cuts | HMR |
|---|---:|---:|---:|---:|
| V40 |41967|23127/16|3211|1278|
| V41 budget |42028|23223/16|3168|1278|
| V42 selector tensor all |42185|23911/16|3135|1278|
| V42 restricted exchange |42005|23191/16|3203|1278|
| V42 gauge exchange |42121|23303/16|3155|1278|
| V42 budget |42078|23223/16|3143|1278|
| PR103 |41533|23143/16|2899|1280|
| V42 peer transfer |41623|23223/16|2866|1280|

All V42 serialized outputs independently re-read and BDD/phase-ledger verified over 3,133,452 legal inputs, with aligned independent source HMRs, data, rotations, classical records and guards equal. Maximum native width remains 37Q. No official verifier or score.

## Algorithm
14 exact V41 piecewise decoders: 3136 invertible selector-basis trials, 14 proposals/13 exact accepted, rejected [10115,10145) phase. This finite GF(2) coefficient tensor is not a numerical PEPS approximation. Two-stage product injection keeps a non-target basis state between steps: form r xor h xor p when [h]=[p] mod target affine span; find the second product by a fixed-first-factor linear solve modulo target span, then jointly solve the endpoint affine map and temporal phase. Search 184 windows (100s cap), 399348 factor solves,13977180 product columns,12 proposals,11 exact passes. All 11 use 2 paid gates (original 1, tensor alternative 4 or 5). The exact rejection at 10115 remains a phase mismatch. Budget DP selects 5 disjoint intervals with +6 E, removes 68 cuts vs V40 and 25 vs V41 budget; SHA 95a59e16e565c7fcc401e278ecfd4636f994c172c87fa67b576b12d9d0d1b186.
Cross-parent PR103: match native words, reallocate scratch classical bit1022, revalidate. 8 distinct matching candidate intervals (one duplicate variant), select 5 disjoint, all PASS. +5 E/−33 cuts/+90 commands. SHA 032375119155cea996b4b75aea958388c4a31e88ae985f91c6b0ad8f7d2c8846. No addition of savings across parents.
Tensor-all SHA 989a7194073170a079d014ac4af12e892c0e77e15e774ef11839faab9b259063; restricted exchange SHA cb261dcf6d50a08c6f819e37db749f8c10404b18b8ec345d590273fc2326cbb8; gauge SHA cfa4fac5fb9e1390326549d63332e98aa37d715c49f54433b72c8ae32ae704b2.

## Source audit / mathematical limitations
User fork corcondor/math README/catalogue: 730 manuscripts/375 families, explicitly research data, not all formalized. Reviewed full CONTENTS catalogue and relevant source sections (not all 730 manuscripts or all code).
- Family107 Staggered extraction over every field: foundations, staggering, joint-extraction, recovery; exact tensor restrictions, shared extraction across stages, distinct histories. Adopted exact finite binary basis change and separate temporal verification, not their asymptotic matrix multiplication construction. https://github.com/corcondor/math/tree/main/preprints/Staggered-extraction-for-exact-matrix-multiplication-over-every-field-September-24-2026/build/sections
- Euclidean geometry in asymptotic spectrum: intro, ports, port-graphs, compaction, catalysts. Shared-label tensor and returned borrowed wires motivate one central representation and precise lifetime tracking. Do not equate spectral prices or bond dimension with CCX or physical width. https://github.com/corcondor/math/tree/main/preprints/Euclidean-geometry-in-the-asymptotic-spectrum-of-tensors-November-24-2026/build
- Family107 Lean scope https://github.com/corcondor/math/blob/main/lean/docs/107.md: recorded exact exponent claims, not independently certified in this experiment. Prior MatrixMultiplication_LeanAudit_GF2 archive only demonstrates classical Strassen seven products, not a finite compiler from asymptotic exponent.
- Family265 PEPS requires gapped Hamiltonian ground state and approximation; no direct application. Family192 Boolean real Fourier/degree, not a GF(2) rank theorem; family135 lower bound characteristic zero, family274 QAC0 restricted model, not GVQCC lower bounds.
- AlphaTensor Quantum DOI 10.1038/s42256-025-01001-1 and Khoruzhii/Gelss/Pokutta arXiv:2602.15285 are relevant finite tensor optimization literature; no RL training or PolyTof port performed.
- Account repo listing 16; 14 root README reads, two not found. Griffith LUT IR and MORTRA typed certificate design relevant, not imported or trained. No unrelated private project contents published.
Lean local tensor identities, gauge, masked relation transport and conditional carrier; whole native verification remains separate BDD. Archive includes runnable search, selected receipts and parents. Full competitive 36Q not reached, best original E1406.3125 not beaten.