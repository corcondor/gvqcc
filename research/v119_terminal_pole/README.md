# Terminal pole audit + V120 native paid reduction (NOT SUBMISSION)

This work is based on actual 900Q binaries, not an independent decoder.
Latest cross-session V119 parent (PR #193 comment 7221922778):
`ae20114bf0c082dde5dbdae9d144d0404bd2c1f5a71dcf435236ca6d086439c6`,
63,214,986 ops, 459,899 static paid, 900Q. Its 4,096-shot mean was 400,574.2707519531 on the peer panel, not a new official score.

## New diagnosis
64 legal matched syndromes (16 w17/w35 pairs j=9 and 16 control pairs j=0) were replayed at tagged boundaries of both CF+Jet and latest V119. All 64 extracted head/tail rows are bit-for-bit equal across these parents. All 16 anomalous w35 lanes agree with the exact GF4096 model for the first 33 finite heads, then have their first denominator pole at head 33 (zero-based), the second visit of the 17th quadratic node. At the scan entrance all 35 true roots are missing (16/16); 48 controls recover every true root with no false roots. This localizes the defect to the extraction/synthesis chart before scan, not to phase correction alone. Does not identify a single first bad gate for all inputs.

In these witnesses, after 33 valid steps, deg N33=3, deg D33=2 and D33=p*g (p != 0), g=X^2+X+k, k=3104. The terminal pole head is stored as (0,0). The existing scalar prefix continuants are p=r, q=border, d=L34, where L is the determinant of the two top coefficient rows. Thus N33 coefficients (in increasing order) are [p*k²/u,p*k²*v/u²,d/p,q] for the finite tail chart and D33=[p*k,p,p]. The finite formula was checked on the actual 16 physical extracted rows, reconstructing the complete exact original rational pair by reversing the 33 finite heads. A paired terminal fold uses N32=h32*N33+g*D33=h32*N33+p*g², D32=N33. The zero-tail algebra uses n0=0, n1=(p*k²)/v (totalized division), including v=0. Synthetic checks 4096 each for finite, simple-pole and double-zero charts; these are not native legal-input proofs for the latter two cases. Guard requires the earlier finite-head and degree invariant; zero head alone is not sufficient.

## Native improvements
- Older CF+Jet parent `992ec337de877c39625c4cf337bf2f740872eca358a25d778e8b679f158571cd`: measurement sink transport 144 unconditional paid gates, candidate `1cd3b0eb8d25f87490db4d081992b4f9064c8556c1f3ca78eb2fc7cf500592ea`; 900Q unchanged. 512 coupled shots, each saves exactly 144; inherited 32 phase errors on adversarial 256 retained, not repaired.
- Latest V119: HMR sink search found zero additional sites. Re-used peer retain_dirty.cpp, cap=64 and period=20000, 37 new exact clean idle-wire product retentions. Candidate `f7a14e0669fcbab7a22a784e11ebb8f9ff6f82bb229c659845d7df1a19cddd9c`: 900Q, 459862 static paid, 63215097 ops. Independent paired replay of 256 official-distribution and 256 matched adversarial cases, original HMR outcomes coupled and extra outcomes arbitrary: all named states/phase/reset obligations match, each shot saves exactly 37. On the separate KickMix panel: 400573.671875 -> 400534.03125 mean, 0/256 ordinary errors, same 32/256 adversarial phase errors. Difference in independently drawn measurement histories means the 39.640625 mean delta is not the exact guaranteed savings. These savings from different parent circuits must not be added.
- The new 900Q candidate is NOT repaired and NOT for submission. No 344k integration, no official 102400-shot result, no score claim. Original private production environment remains unavailable.

## Verified Lean
Lean 4.35.0 + mathlib v4.35.0, strict warnings and axiom audit:
https://github.com/corcondor/gvqcc/actions/runs/46025000346
9 TerminalPole statements + 7 RollingTail statements; 16/16, no sorryAx or Lean.ofReduceBool. HMR/retention Boolean theorems axiom-free. These are local mathematical laws, not whole-circuit formal verification.
Peer #194 direct codec audit also passed https://github.com/corcondor/gvqcc/actions/runs/46021719041.

The actual full KMB, replay/source archive, edit records and native state traces are supplied in conversation. Next integration boundary is final_decoder/decode.py synthesis and tail_join consume, preserving both forward and inverse/HMR phase tokens. No merge or submission.
