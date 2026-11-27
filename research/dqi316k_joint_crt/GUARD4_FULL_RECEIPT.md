# Measured results — NOT SUBMISSION

Original 316K lineage only. No 410K substitution, no score claim.

## Four-product guarded inverse

Replaces the 6 paid GF8 inverse/gating products at each of 4095 points in #237 with 4 shared ANDs, an invertible affine output frame, and exact HMR cleanup. All 16 input tuples exhaustively verified. On Vercel session sbx_BB3FRj9yNqtRpsEkqW5V3PN4498m, command cmd_476e9c510fce48d3ac24e2293bc9, native KickMix 1.0.0: 880Q, 215389 static/mean paid, 18282283 ops, SHA256 d677343b5d7d115b8eea4dc306655eb221c5c76f23fc7a9ec9688a2f2218ce22. 216 inputs including 96 all-pole cases, two seeds, 432/432 value/phase/ancilla/mask checks passed relative to chart contract. Saves 8190 paid vs #237; ops increased 364455. Independent strict Lean 4.35.0 and complete chart native CI 46077791127 both succeeded; six local theorems axiom-free. Artifact 15236221095 independently matches Vercel hash. Identity on the complement: NOT full DQI.

## Physical integration of complete original 316K tape optimizations

Parent #240 16c55293caa7408caee6fdfc05b7efd0e28a51918626c48838506f25044a72a6 includes #224 loans, #226 18494 early HMR movements, remap and four CCX folds. On that actual tape, full_unified.cpp removes 1558721 pairs and 18 paid gates in provably inactive classical scopes (16 CCX/2 CCZ).
New local KMB af12d490a8e190642675b0b801b59adbaeeeea93f935f9b52225c579ebb3e2ba, 900Q, 66724227 instructions, 318950 static paid (312234 CCX, 6716 CCZ), vs original 318972 and 69782188 instructions. The two-stage executable reproduced the exact candidate hash. Paired KickMix replay 622 legal inputs: both candidates have 452 value and 226 raw phase errors (overlap; union 456), zero dirty and mask errors, all output arrays identical. Mean paid 316126.6720257235 on both; no measured score improvement. Vercel full-tape replay of this new hash was NOT completed; this whole-tape native test was local. Width remains 900Q. Does not incorporate the expensive chart patches because they violate cost/width and do not remove all counterexamples.

#239 independent Vercel 102400-shot score replay belongs to another hash, with cost 305042060052.2295 vs historical donor 305041647011.3978. Not a new official score and the strict forced panel fails. #238 integrated expensive tape rejected (120/338 inverse-transform stress failures in original receipt, 3690518 paid, 901Q). The shared root chart must replace, not append to, existing arithmetic; the total syndrome-to-canonical chart and physical 898Q packing are still unproved/unimplemented. No main merge or Kaggle submission.
