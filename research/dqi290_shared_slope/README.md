# #289 shared slope compact reduction (research)

The native parent is the exact #279 full KMB 518d634ede9dcf7e78a8e91264db25d544f54bf3c86caee7ebc355f618a66499.
The decoder remains unchanged. Build slope table once per anchor, sort only the sampled prefix, then count candidates using the same table. Modulo-32 support count is a lower bound; strict acceptance is fail-closed. Remove 2310 sentinel comparators and reuse the exact 4024 in-place linear frame maps. #280 frame contractions retained. #284 and #287 proof suites are references, not claimed as a native splice.

Matched 2048 ordinary shots, seed 20261128, four error counters:
- #279: 316151.99658203125, 67549292 ops, 318333 static paid.
- #289 compact: 316151.49169921875, 67262375 ops, 318344 static paid.
- shared 1x1024 K2: 316151.49169921875, 66786263 ops, 318344 static paid, SHA256 2545a84896ba44152eab0db6856a056d23f60869c60fac8e7d1a8788c51e88dd.
- shared 2x1024 K2: 316150.9814453125, 69776734 ops, 318344 static paid.
All above 900Q, zero value/phase/ancilla/mask errors.

Rejected exclusive lambda/mu phase-kernel experiment: 318333 static paid, 75918966 ops, 316130.83251953125 mean, 2 phase errors / 2048. Do not submit this variant.

The #289 compact KMB completes independent 102400 reference-distribution shots in a streaming replay (empty salt, batch 256) with zero four-counter errors, mean 316130.385859375 and reference formula cost 305040840623.9224. No private salt or claim of official Kaggle score. Known low-weight defects are not repaired. The shared 1-anchor candidate has a separate replay. Final receipts and complete C++ sources are in the accompanying local archive; this PR contains mathematical lemmas and audit notes. Fix #289 origin-slope zero multiplication simplification and add strict Lean lemmas for sentinel pruning and sound short counts. No main merge or actual submission.
