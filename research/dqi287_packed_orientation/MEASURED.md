# Native packed orientation follow-up (2026-11-28)
Recovered the archived #285/#287 executable sources, exact five unsupported fixture indices, KickMix 1.0.0 and exact #274 physical shell. #287 compact KMB decompressed and SHA256 matched 0660a0dd8301753b87ee21db0be2b1197df8d3fbd4cdd350b12cae98bc25856f.

At every scalar-first pivot, orient the source pair by its zero test. Retire (alpha,r) with alpha=a/h nonzero; if originally swapped, r=0, so swap the retired words to (0,alpha) and clear the flag from the first retired word. Reverse this at return. No extra stacked orientation bits. Does not implement nonfirst or alternating pivot elimination. The new algebraic orientation-packing proof is in AnchorPivot.lean; CI outcome must be checked independently of native tests.

D,N phase component (KickMix 1.0.0): #287 886Q/204605 paid/8682512 ops -> 886Q/214169 paid/8697884 ops. Exact inherited 1024-shot panel [value,phase,dirty,mask] = [10,7,0,0] -> [4,1,0,0]; indices 83,377,420 repaired; 137,292 remain. Captured 144/144 clean. SHA256 a02cca13f8b612302ee6b9a95f64e6a5245d6c8354a6dae59256da8b6da7de58.

Alternative repeated-anchor confluent chart 886Q/204605 paid/8805306 ops: 2 value and 2 phase errors on 144 captured shots; rejected because of new regression.

Native first-pivot priority tag compute, inverse and diagnostic phase: 898Q, 3729 paid per direction, 7458 compute/phase/uncompute; 6912 shots total across three variants, no input/tag/orientation/ancilla/phase errors. Selector alone, not the missing elimination circuit.

Physical raw-S splice: exact #274 shell SHA256 e2c07b6b04dd74c298581090d93e1925df985df0f039440dc644751205e8c037; sentinel at op9758919, 852 D,N bits, 13 retained and 35 scratch. Map #287 D0..34,N0..34,D35 correctly to shell D0..35,N0..34; preserve public mask bits; relocate private classical bits. #287 baseline and repaired kernel both physically fit 900Q. Static paid 424234 -> 433798; operations 32298693 -> 32314065. Candidate SHA256 7d3c7e4d412412fb0b2b68de131d4190a945385a4e538f908b9cefff80c18946.
Matched raw-S replay [value,phase,dirty,mask]:
- Independent 996 stratified shots: [9,4,9,0] -> [6,3,6,0].
- 1024 distribution shots: [6,1,6,0] -> [2,1,2,0].
- exact saved 622 counterexamples: [5,3,5,0] -> [2,1,2,0].
- 144 dense all-weight shots: [3,2,3,0] -> [3,3,3,0]; phase regression.
All are a comparison within the same #274 shell, NOT a repair of exact #257+#279. Paid cost increases; not a competitive candidate. No official salt/score claim, no submission, no main merge. Complete executable source snapshots, KMBs, replay data, hashes and receipts are bundled in the accompanying research ZIP.
