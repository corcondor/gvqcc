# Guard-span cache and contextual phase fusion (research only)

This branch continues PR #298 (f9792720e702cb238992253673683fb0be17e0f2) and ports the #297 guard joint pass and earlier contextual guard pass onto the recovered #280–295 fusion tapes. The original #292 portfolio is unchanged; neither new candidate is a certified submission.

## Full DQI native tapes
Frozen #292 DQI SHA256 2545a84896ba44152eab0db6856a056d23f60869c60fac8e7d1a8788c51e88dd.
Recovered fusion joint parent SHA256 1a8d9436b5a9af308e1adfbe391776102e77b51029933c80764b667e5b6cc1c5 (318263 static).
Recovered fusion compact parent SHA256 b933895e95aa4a976a0a83edce9674b1ba20b7fc9dbe8d3903e14dddd1af64a1.

- Six #297 joint cubic sites remove six CCZ in each fusion tape.
- Contextual abstract Boolean guard analysis removes 261 statically inactive CCX, with no executed paid reduction for this pass.
- Joint output: 900 Q, 317996 static paid (311202 CCX, 6686 CCZ, 108 CSWAP), 87704819 ops, SHA256 a8b5c62e24e7e44818bd46d75f8fa00a2bb9de64965c8c07912637dd58d7ebea.
- Compact output: 900 Q, 317996 static paid, 66738240 ops, SHA256 e30af532ef33c587d07c251b4209ae9ea0fc1beda3967cb0b22761a4f3f8ba60.

KickMix 1.0.0 paired replay: 1024 distribution, 622 saved, 144 dense-weight cases. Each 318263 fusion parent vs final output: all four register/phase/mask difference counters zero, same executed paid counts. Exact #292 vs joint: ordinary errors 0/1024 both, mean paid 316099.98828125 -> 316094.017578125; saved failure union 456 -> 411 (raw phase 242 -> 210); dense union 70 -> 70. Improvement relative to #292 inherits the prior #294 gauge/covariance; do not attribute runtime gains to static guard deletion. Different panel than earlier 2048/8192 reports. No 102400-shot final replay, private salt or official score.

Reproduce: use archived GVQCC_280_295_Fusion_Pipeline_RESEARCH.zip and the exact fusion KMB parents above. Build guard_joint.cpp from #297's research/hmr_multimeasurement_20261128/guard_joint.cpp and its original cubic dictionary implementation from the #295 archive; execute it on either parent; compile this directory's contextual_guard.cpp with g++ -O3 -std=c++17, then run contextual_guard intermediate.kmb output.kmb removed.tsv. Exact original sources and paired harness are in the accompanying research archive.

## New #298 converter synthesis
For a fixed rank-42 field multiplication tensor with left forms L_j, partition those forms into subspaces of ranks 6,6,6,3. Cache g L_basis in six already-clean workspace wires; reconstruct each guarded linear form by XOR. Share the same cache over disjoint-target updates. Erase cache by HMR, repaying m*g*L_basis by conditional CZ. Fixed compile-time groups depend only on the tensor, never on syndrome, sampled error positions, or measurement outcomes.

In guard_span.py (run alongside recovered #298 gauge_joint.py from DQI_Joint_History_Free_Gauge_RESEARCH.zip), the exact fixed rank-42 tensor passes 288 bilinear basis/guard cases. Coefficient identity is checked on 172032 measurement-basis assignments. Isolated multiplication compute CCX 84 -> 63. Actual generated #298 converter: 190110 -> 183642 CCX, 3276015 -> 3238175 ops, unchanged physical 900 Q. 704 captured and 288 fresh solve/source/scratch/phase cases pass, but all 60 higher-confluent obstruction equations still fail. No full-domain claim.

Splice the emitted physical converter into the exact archived #274 raw syndrome shell using #298 prefix_splice.cpp: prefix paid 292176 -> 285708, prefix ops 13035062 -> 12997222. SHA256 baaee813a0696baec895aabe4b41b6d300d0e0ebf308a5395f654241b3f15998. Independent native bit-sliced capture_phase replay: 576 distribution and 128 forced syndrome inputs; all 900-wire checkpoint values byte-identical to #298; zero within-prefix phase delta. This is a prefix with no completed closing/phase oracle, not spliced into 317996 tape.

GuardSpanCache.lean formalizes local Boolean distributivity, debt cancellation, inactive CCX, and the exact decoded mask dictionary. It does not certify the entire compiler or oracle. CI status must be checked separately. #296 ghost projector remains separate: 21 invalid charts unresolved. No full-score or all-error-zero claim.
