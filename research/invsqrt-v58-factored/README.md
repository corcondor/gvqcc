# V58: factored carry and exact legal-interval contraction
Research only, NOT SUBMISSION. Independent branches of research: PR138 arithmetic and PR136 signed-coset full oracle. All new circuits Q<=36. Native custom serialized replay, not official KickMix/Kaggle verification. No main/score/submission change.
## PR138 same signed two-stage stream
| Variant | Q | CCX | E (CCX + half guarded CCZ) | ops | snapshots or actual R |
|---|---:|---:|---:|---:|---|
| PR138 |30|1237|1278.5|8614|742 snapshots|
| dyadic |36|985|986|5668|742 snapshots|
| arbitrary weights |36|964|965|5136|744 snapshots|
| direct phase |36|964|965|5880|744 R|
| triple |36|1430|1586.5|9330|622 R|
| factored triple |36|1306|1307|9054|622 R|
52 address masks and 90 mantissa monomials, 4 cached low address ANF monomials, high-selector affine care set, signed integer weights, product cover. Factored triple moves 122 carry compressors before the shared coefficient multiplication; 1218 HMR phase coefficients cancel. All 3,133,452 legal inputs, restoration and exact weighted phase modulo 2^32 verified. Final SHA256 8f3183bdf799fe684cd0e86d1c601321e83e674c31660e310b48d5e53e40576f. Same stream hash e4a7a79b75dbca5f375f48fb94ab52e3da0e987ca4b773844223d64b18041292. Compare PR140 E1034/R707: fixed proxy E+(239.00391117857393/33)R 6154.48 -> 5811.86, ~5.6% reduction. Not exponent-scaled or remaining-stage phase, so not whole-oracle cost.
## Full 25Q lineage
Exact PR136 signed coset plan: 5338 CCX/8464 generic R/91724 ops/3058 HMR. 26Q 4871/8429; 36Q 2071/8464. All full 2^22 input controls, modular 128-bit phase and all 3,133,452 legal tolerance checks pass. Implement measured prefix recursion with exact affine-line prefix transitions and globally select direct phase versus toggle plus compensation. Then integer interval95 coset deletion 7427->7278 in 2.90 s. New approximate phase, exact against its own plan: 25Q 5234 CCX / 8280 R / 89392 ops / 2984 independent HMR, SHA256 10dc8a002dede573a3355dd1ef26d65e7e603440931c78ef6fdefdbfbf64ebb6. Full serialized replay PASS in 6.11 s; worst normalized tolerance .9496700186. Fixed product proxy 1,630,056 vs PR131 Q25 1,760,012 (-7.38%). Still far above incumbent ~60927.55; no official score.
## Low-rotation specification (not complete native)
Two searches, 864 configs each; stratified 68,586 legal samples, 54 full-domain integer evaluations, 31 accepted, measured 11.69+14.69 s. Radix2, single master with odd exponent constant scaling: two-multiply spec 336 retained product candidates vs 969 in PR132 quartic, loader rank proxy374, min margin13,735,429. Robust 362 candidates and margin51,343,783. Folded parity profiles remove extra sqrt2 constant multiplication: two-multiply 336 product candidates with larger loader proxy; robust cubic 498 product candidates, margin51,343,783. No physical width, CCX or 31-rotation full-oracle claim for either model. PR139 Booth costs are estimates, not full verified native costs. Need true bounded-width consumer, inverse, exponent compensation and rotation synthesis; no noncompetitive submission.
## Reproduction
Complete native compilers, source templates, tags, data and receipts in delivered research archive GVQCC_V58_Sub37_IntervalTransport_NOT_SUBMISSION.zip (147 files, SHA256 3e644b14b67f2045ea37199eb8114d7a6c82fea2bd51cfa46de66f937edafec0). Lean local lemmas only, CI configured. No cross-lineage cost addition.
