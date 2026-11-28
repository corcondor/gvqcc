# Complete low-cost artifact reassembly (review only)

Retrieved exact #299 Joint DQI KMB (a8b5c62e24e7e44818bd46d75f8fa00a2bb9de64965c8c07912637dd58d7ebea), V111 chemistry (15 ANGLE files + matching NPZ), and V112 27362-op InvSqrt (a545e8cf34f95cfbdaf0db475409e3a56dc4edefe3010cc5fa6cf4af89797e1a). Assembled new 18-member review-only ZIP SHA256 d552bf1f773ca70e34db7d88b8c8754f0a7f70d9e67581e79f4d7487498e3cec, 111424330 bytes; CRC and all member digests checked.

Paired independent C++ replay of the same 102400 inputs and measurement coins:
| DQI | Q | static paid | CCX | CCZ | mean paid | union errors |
|---|---:|---:|---:|---:|---:|---:|
| #292 | 900 | 318344 | 311519 | 6717 | 316132.1029589844 | 1 |
| #299 Compact | 900 | 317996 | 311202 | 6686 | 316131.60161132814 | 1 |
| #299 Joint | 900 | 317996 | 311202 | 6686 | 316126.4307519531 | 0 |

Known stress failures remain. Not a proof of better distributional failure probability, not new official verifier or private salt. Fixed covariance can move errors.

V111 chemistry: 3262 CCX + one conditional CCZ, expected 3262.5 paid/pass, total expected Toffoli 13025, 405Q, cost 247478615.98392352. Past two-salt official-source receipts match all 16 member hashes; prior memory allocation adaptation. New independent exact 36570 transitions, 3012 HMR coefficients, 3671628 coefficient-address checks pass. V112 InvSqrt exact prior official-source receipt for 200540928 shots matches file hash, not rerun here; expected paid 11237/8, 37Q.

Additional whole-tape commute/pool, affine HMR sink, CCX/CCZ sharing and cubic plane searches found no new paid reductions on compact or joint. V111 exhaustive reachable two-direction live affine span scan on all 3262 CCX: 0 replacements. These are limited rewrite classes, not lower bounds. #303/#304 partial savings are not spliced into the complete circuit or double-counted.

Conditional old local score 33.3355088809884 -> 33.34244155360765, assuming same error correction factor and fixed other conditions. At 900Q target mean 315627.53075, about 499 additional paid reduction; 899Q unchanged mean conditional 33.36716. Not an official measured score. No submission or main changes. Audit/source ZIP and complete research-review ZIP delivered separately.
