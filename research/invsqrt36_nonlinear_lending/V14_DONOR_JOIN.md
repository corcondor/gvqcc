# V14: deterministic V13 donor integration (research only)
Common parent PR59 wide SHA256 ea605794431d64a22de189087a6c637bf73650b19068dff106755a1798576eca. Exact source archives recovered from Library: PR61 b781f4c0945cc2d732138b1d49f59c21f6e663d89b5431ece3a10a8e52ee4c57, PR62 8c35307449bcbeeb35438afdcfaa13f8e1a2752b788cb67fc877812165d98d9f. Source-level history exclusion still incomplete (four older ANGLE archives); no novel exploration. Only deterministic integration of already verified donor lists.

|track|ops|static paid|expected paid|source coverage|peak Q|BDD comparisons|
|---|---:|---:|---:|---:|---:|---:|
|PR61 cost|40079|1833|1668.9375|55567|37|peer|
|PR62 wide|41851|1877|1698.9375|56059|37|peer|
|joint economy|41071|1866|1694.4375|56059|37|40772|
|joint hub|41118|1882|1710.4375|56184|37|40724|

Common parent provenance: collapse PR61 history+null-frame chain, or add deferred cubic+hub chain; preserve every old gate list, replacement, and original HMR identity. 812 economy or 816 hub intervals all disjoint from 29 gauge intervals. Keep gauge normalized-record phase pruning and relocated HMR atomically. Native header arity-three count repaired; other sections preserved. Actual native SHA256 economy bc688108596a21e8a48fdd1b172b40e60b4fb4b405594c938709904cc1b25135, hub 5938ec61a11358b8cf03b4ba6003c7bfcbeccacc0e91ceffd39a6748185b4f81. 537/529 q36-touching operations, peak37Q. Both exact direct BDD replay PASS for all 3,133,452 legal x and 1,186 original independent HMR variables; 5 events removed, exact sign ledger empty, final data/classical equality and all compared rotation masks/guards equal. Full replay first timed out at 60s; synchronized-state fast path reuses the same unchanged operation once only when data/classical/guard/stack agree, independently replays changed spans and mismatched records, exact ledger retained. 23.64/22.29s, 38,708/38,656 synchronized unchanged comparisons. No sampling. Reuses peer BDD engine, not official KickMix.

Economy strictly improves PR62 at same coverage (-780 ops, -11 static, -4.5 expected); hub adds 125 source instructions over economy, costs +16 expected. Separate Pareto points; PR61 cost remains cheapest. Full36 break-even E<1452.05390236114; economy requires >242.38359764 and hub >258.38359764 expected reduction. All 37Q; no official score or submission. Source coverage 92.2539%/92.4596%, not width.

Lean: PR61 CI 45385414051 and PR62 CI 45385597849 confirmed success, candidate-local only. JointV14.lean certifies actual receipt totals and ten chart records; CI separately configured. Companion archive includes full per-edit resource Lean source (all 841/845 ordered intervals and chart bounds) generated from native bytes, not executed locally (Lean absent). No whole-oracle Lean claim. Reproduction: GVQCC_V14_Joined_V13_92p46_NOT_SUBMISSION.zip SHA256 230e987d51a318050d7b7ae6cea056b11e44eff4c9c59850b2329f49a0514685; bash REPRODUCE.sh; contains both parents, exact JSONs, full KMBs, scripts, logs, Lean generator and source.

References for measurement-aware compositional verification:
- Hong, Feng, Li, Ying, Equivalence Checking of Dynamic Quantum Circuits, ICCAD 2022, https://doi.org/10.1145/3508352.3549479 — dynamic-circuit instruments and decision diagrams.
- Ricciardi et al., Quantum Circuit Equivalence Checking: A Tractable Bridge From Unitary to Hybrid Circuits, https://arxiv.org/abs/2511.22523 — deferred measurement, separation/projection.
- Sander, Burgholzer, Wille, Equivalence checking of quantum circuits via intermediary matrix product operator, https://doi.org/10.1103/3q71-y8cf — cancellation-aware verification of unitary regions.
No claim these methods are implemented verbatim or unique across literature. Main unchanged. No Kaggle upload.
