# V52: width is a variable, not a 36Q requirement

Research diagnostics only / NOT SUBMISSION. Parent is PR117 V51 quantized80 plan, reference SHA 57316aacce41f47eca1c023dee1456b83091dd21d182f5ae14acad447df42b45. Same approximate analytic phase, NOT exact PR92 source equivalence. Full 22-bit binary input requires 22 physical input qubits; no proof that competitive cost requires 36Q.

| Q | CCX | native ops | arbitrary rotations |
|---:|---:|---:|---:|
|22|55606|115245|15287|
|23|5920|48570|15280|
|24|2720|44616|15280|
|26|1378|42852|15280|
|28|914|42382|15280|
|30|676|42122|15280|
|32|544|41952|15280|
|34|464|41818|15280|
|36 (PR117)|160|41002|15280|

All new native KMBs were independently reread: every rotation control on the entire 2^22 cube, all input/work restoration, modular phase cancellation, exact squared analytic tolerance on 3133452 legal inputs PASS. 22Q additionally reconstructs actual serialized phase and compares to the original V51 plan on all 2^22 inputs modulo 2^64 turns. Worst analytic error ratio 0.7998046875, x=1048576. No HMR. No official verifier or physical rotation synthesis test. This is a finite tested width sweep, NOT an optimal Pareto frontier or proof of low-cost feasibility. 22Q SHA 6cd42337788b96b536f6340cc9d8b948c958c45d8ad3871b7bf2fbea6da7f268; 23Q SHA fb51b28e1f9c723e1585d5dc1092e535050d07d63e4ba95f0afd227624fa1d2c. Full source, plans, all native circuits and receipts in companion GVQCC_V52_WidthPareto_NOT_SUBMISSION.zip.

## New construction
Let f be a prefix indicator and r a parity involving a target input bit outside the prefix. A borrowed-input controlled toggle changes r to r XOR f. The signed phase identity (r XOR f)-r=f(1-2r) gives the block Walsh term, using no persistent flag. Restore the borrowed input after each group of parities. Split the constant prefix term using 2[p AND b]=[p]-[p]chi(b) and its complement, recursively. For a prefix with 21 controls, split its last bit out into two signed terms so at most 20 controls remain, leaving one dirty borrowed wire. Coefficients are exact dyadic integers modulo 2^64 (checked divisibility). The x=1 singleton is a full turn and vanishes. Separate absolute constant implemented by opposite-polarity rotations. This is a finite phase-adjoint/transport construction, not a port of OpenAI's asymptotic FFT/matrix algorithms.

For 23–34Q use an adaptive prefix/suffix decomposition with variable clean slots, exact dirty multi-control ladder and sibling transport. No new mathematical necessity for 36Q. The low-rotation branch remains the priority: ~15k rotations cannot compete with 32–33. The 22Q construction is an existence witness, not a proposed submission.

## P0-B low-rotation progress
PR116 captured frames: dropped root3 has exact target-free quadratic representations at rotations 4,14,31,36; term counts 17,14,24,23 respectively (constant/linear terms included). Sample pivot 8192 rows; each positive relation independently verified on all 3133452 legal inputs. No affine replacement found in the recorded scan. Tested all nonconstant binary truth tables combining root3 with these four retained roots except unchanged old root: 52 sample LP screens. Two completed exact whole-domain refinements (roots36,31, table5) failed with 187/193 violating inputs and worst ratio 1.0715439692139626. The longer refit search was interrupted, not a proof of infeasibility. No new competitive 32-rotation circuit. Do not repeat the same binary-table screens; use joint >=3-root/predicate repair and cost-aware arithmetic. Preserve distinction between analytic tolerance and rotation synthesis margin.

## Updated task priorities
P0-A: minimize actual official cost over width >=22, not hardcode 36. First beat 37Q incumbent; 36Q remains a milestone, not goal definition.
P0-B: 32–33 rotations + low native paid gates + bounded-space shared evaluation. Primary bottleneck.
P0-C/D: integrate long-distance carry/data/phase transport in original small-rotation circuit. Diagnostic low-width progress alone does not close these.
P1-A/B/C and P2-A/B/C remain open (local implementations/proofs exist). Four-theory roadmap from PR117 remains valid. Local Lean identities below prove the algebraic steps, not complete native semantics or score.
