# Reciprocal-coordinate loan — research, NOT SUBMISSION

## Native full 897Q circuit
Parent lease897.kmb: SHA256 352acd5a84f6d90004ec801597036793e271630783252b54f6a10f7faf3927f3, Q897, 437300 static paid, 48886415 ops, mean 413587.6740722656 (4096 fixed distribution shots).
First pass: Q897, 437293 static paid, 48886449 ops, mean 413581.3835449219, SHA256 42743da957fe5d419a861f867f27a06d3d63fa45b5cb2b33cadf7fed19256054.
Second pass: Q897, 437256 static paid, 48886597 ops, mean 413543.8308105469, SHA256 1a878801d16c7378ff68cd6e1d75cf7b2a19bf1b7e262c22aca6aa3eddeb6983. Second pass accepted 37 existing clean leases with a longer search window; no affine-reconstruction endpoint was accepted.
Both new binaries: 4096 fixed distribution + 256 forced weights/position52 + 1728 matched + 1334 CF hybrid and inverse-rotated panel shots, all value/phase/dirty errors zero (mask restoration checked on last 1334). This is not official verifier, official score, or all-domain proof.

## Local native frontier
Supplied nonzero GF4096 scalar s and reciprocal t=s^-1, independent payload x. HMR a coordinate of t, use as workspace for y=x*s; recover the coordinate via conjugate(s)*N(s)^-1, use N(t)=N(s)^-1 and recover x=y*t to repay all measured phases. Multiple coordinates are possible; for k>=3 use 3 cleared coordinates to hold the GF8 leaf during GF64 inverse.
Unconditional scratch 12/11/10/9/8/7/6: paid 42/92/98/104/110/116/116. Native test each mode 14334 forward and 14334 roundtrip, all zero errors.
Conditional two-payload scratch 12/11/10/9/8/7/6: paid 120/171/180/192/205/222/227 using streamed phase bank. Each 16380 forward and 16380 roundtrip, all zero errors. Initial single-coordinate version cost 193 static; direct phase expansion for scratch6 cost422. These were improved by streaming the masked linear forms.
Masked two-payload product scratch 12/11/10/9/8/6: paid 96/97/100/106/113/129, 16384 shots each, all zero errors. For scratch11, share 10 masked coordinates and stream the three nonzero linear forms on a 2-dimensional quotient.

## 896Q generation
Three strict cap=896 attempts: (1) original scale fixed, then cscale 885+12; (2) cscale fixed, then masked_products 885+12; (3) shared bank fixed, forward extraction, synthesis, conversion, scan, unconvert and unsynthesis all completed, then reverse extraction failed at selected_zero: 896 live + 1. No full 896Q binary from these three attempts. Width allocation failure is not a lower-bound proof. Separate attempt applies the existing copy-free reverse route to nodes 16 and 15. Only completed checked binaries may be claimed. The historical 316k decoder's all-input repair remains unresolved.

## Lean
ReciprocalLoan.lean: 14 local theorems, Lean 4.35.0 strict run https://github.com/corcondor/gvqcc/actions/runs/46047688034 success at f320acaa85d3f314c0c562d612eebb9c2d4fe974. No sorryAx or ofReduceBool. Does not certify the entire native tape. No merge or Kaggle submission.

## Completed fourth attempt: 896Q
NOREPLAY_NODES=16,15; conditional stream and masked bank applied. All stages ran through. Raw full 896Q: static paid 444701, ops 61864345, mean 421779.3684082031, SHA256 d3be8e2788e1900f68dbd6ab13137d008ae1acd99e3eba7b34d1716b38d1b4e6. Native 7414 shots clean. Exact direct cancellation: removed 11082102 ops, 436 paid, inserted 144 unpaid instructions, output Q896, ops 50782387, static paid 444265, mean 421343.3684082031, SHA256 e8c8cc46ce177afcb2df62c9e1dfda0d6edeac9ff4ecc79de0ac428ec16d2793. Replayed 4096 fixed distribution + 256 forced + 1728 matched + 1334 hybrid/inverse-rotation = 7414 shots again, value/phase/ancilla errors all zero; classical mask restoration checked and clean for 1334. Same error penalty assumption Q²*T is 1.65898% worse than final 897Q, so this is a width milestone, not a competitive score improvement. No official verifier run, full-domain proof, or submission. New binary and reproduction scripts delivered separately as research ZIP.
