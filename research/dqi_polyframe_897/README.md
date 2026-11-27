# DQI polynomial frame width exploration (NOT SUBMISSION)

Parent is V124 #205, SHA256 5dd23729f644940b807235da50eefdf0cfad2b8477f6f874020427c0d7149e05, Q898. Historical 316k donor has restoration defects (#208); #209's 316131 mean is an external conditional branch replay, not a coherent replacement KMB.

Conservative whole-tape zero-lease recoloring: 51,151,625 original instructions, peak 898 at operation 3,678,213 (zero-based). 821,903 instruction boundaries at width 898 when input wires can be reassigned and restored. At first peak, 11 known equal/complement coordinate pairs. Static exact dependency/virtual affine and higher-degree polynomial experiments: hard cap 897. Original HMRs and classical records retained. Immediate phase-repayment terms used as reconstruction witnesses ONLY when exact symbolic equality to the pre-measurement value is checked.

Best tested prefix ends before original operation 4,575,251 (three consecutive HMRs on 894,869,870). Remaining virtual logical coordinate 892 depends on all three measured coordinates, plus 871,889,896; cannot free or materialize under current synthesis cap. No width lower bound claimed.
- Parent prefix: 898Q, 4,574,307 instructions (markers stripped), 37,287 static paid, SHA256 7239815b9f24808ffd7f945f007d398b1a138b3409bee61123d88e47e329811b.
- Candidate prefix: 897Q, 4,693,922 instructions, 182,918 static paid, SHA256 bbb778e4aeb2608970421f31a0cdc62ebf6e93dc7f2561e97018920498c59558.
- Fresh KickMix 1.0.0 paired simulation: 128 legal balanced-weight and 128 arbitrary syndrome shots (two independent measurement seeds), all 898 reconstructed logical values, phase, all classical bits, unused physical zero wires match; 256/256. Decoding at the cut is an external exact polynomial map, not an emitted full DQI output stage. Candidate is rejected for cost and incomplete width coverage.
- Full generator hard-cap 897 trial timed out at kit loading; no circuit emitted.

PolyFrame.lean formalizes generic Boolean substitution and inverse transport, affine pivot, dirty-control synthesis, phase witness and repayment. These are local semantic laws, not proof of the complete KMB or the C++ symbolic analyzer. CI must pass at its exact commit. Original main and Kaggle unchanged. Full code, actual prefix circuits, reconstruction map, and test receipts are in the owner's companion ZIP. Next approach: retain factored product expressions rather than expanding to monomials; use the original decoder's exact HMR group recomputation witnesses. No 897Q full decoder, no new score, no claimed paid-gate improvement.
