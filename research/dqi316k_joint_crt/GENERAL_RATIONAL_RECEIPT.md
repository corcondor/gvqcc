# General rational phase scan and full-tape specialization splice (research only)

Vercel sandbox `gvqcc-316k-general-norm-scan`, session sbx_SJKiWg1PtnoBWVbV5LwWr9yvnR2d. Actual KickMix 1.0.0, NumPy 2.2.6.

Recover earlier November 19 phase58 machinery from user archive gvqcc_fusion_sources_20261119.zip (joint_norm_coefficient_42.json ring_terms and phase16_template.kmb, converted to exact KMX). Reuse #237 rolling evaluation, HMR repayment and tower basis. Unlike the G-allpole scan, the numerator P is an arbitrary quantum polynomial. The canonical interface is 35 nonleading coefficients of monic degree-35 D and 35 coefficients of P. For weight w<=35 pad both by X^(35-w), preserving all nonzero-root amplitudes. Classically transpose the binary mask into field trace-dual lambda; produce lambda*P(x) in scratch. Compute norm and cross coefficient using the exact 42-product dual-number tensor. Gate the 6-bit cross coefficient by the true root bit. Use the earlier 16-product zero-safe GF64 phase template. Static paid per point = 42+16+6+11 = 75. HMR repayment and restoration of every public mask. The narrow variant clears and recomputes the mask-weighted numerator and reuses those 12 scratch bits, reducing width by 12 at no added paid gates.

| variant | Q | paid | instructions | full 4095-point native validation |
|---|---:|---:|---:|---:|
| general_scan |891|307125|47114795|320/320|
| general_narrow |879|307125|53568515|320/320|

144 legal inputs (4 per weight 0..35), 16 arbitrary canonical pairs incl repeated roots/zero derivative, two seeds. All four errors zero relative to canonical phase contract. **This is NOT the complete syndrome-to-rational decoder**, and the 307125 cost does not include it. The prior 215389 special scan and the 307125 general scan have different domain and cannot be compared as complete DQI score. The original 316K donor has no exact historical phase16 contiguous opcode template (full match 0); no validated D,P physical seam. Do not add this full scan to donor. The decoder and phase integration remain open.

Physical #238 full tape follow-up: replace both old #237 4095-point scan regions with #241 four-product specialization, checking every operand through an injective physical map. Preserve the existing #238 decoder, low/single/all-pole repairs and mask transport. Exact output hash in full_guard4_receipt.json. 901Q/3674138 paid, vs #238 3690518, saves 16380. Local actual KickMix 1244/1244 saved, 338/338 cross, 576/576 fresh. Inverse-Frobenius stress still 119/338 failures (116 value, 58 phase with overlap); no repair or score improvement claim. This whole-circuit experiment was local, not Vercel, and remains expensive. The generalized 879Q canonical scan was NOT spliced into the full tape. New files on research branch only, no main merge/submission.

Lean GeneralRational316.lean adds 11 formal statements incl exact 144 basis tensor checks, projective padding, norm/conjugate law, guard and resource accounting. Strict CI must pass before claiming new formal certification.

Reproduce generic phase: python general_scan.py --count 4095 --cases 4; python general_narrow.py --count 4095 --cases 4. For #238 full physical specialization use the pinned #238 source archive with append_hermite.py, splice237.py, audit fixture binary files and native_full_replay.py. Pinned old #237 hash f99e60190524fe0121ee5216d4a94195d49cfd31d9f6fe5eeaf06faa81e1bccc; new #241 d677343b5d7d115b8eea4dc306655eb221c5c76f23fc7a9ec9688a2f2218ce22. Execute splice_guard4.py PARENT OLD237 NEW241 OUT and native_full_replay.py OUT receipt.json.
