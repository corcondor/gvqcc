# Complete native mask residue oracle (research, not submission)

Parent identity shell: PR #274, artifact https://github.com/corcondor/gvqcc/actions/runs/46118385566/artifacts/15252148613 . SHA256 e2c07b6b04dd74c298581090d93e1925df985df0f039440dc644751205e8c037. The shell uses coherent weighted D,N conversion and closing, not a finished half-GCD implementation.

Final KMB: fd713f141f7856988fd01714eba56b716033708dd4e809b67068e7c687aa7d52 (uncompressed). 900 Q, 89193558 instructions; CCX 428217, CCZ 123759, CSWAP 1728, static paid 553704. Shell 219629; residual scan 334075.

Fixed public interpolation on first 70 nonzero field points fits m_x/x; compensate on input by trace pairing against S, then skip those leaves. Remaining 4025 use coherent root guard, in-place masked numerator and retained inverse norm. No host syndrome-dependent branch or mask optimization against verifier randomness.

Native KickMix 1.0.0 replays: 1440 saved panel zero errors; 996 structured panel zero errors; ordinary reference distribution 1024, union 1 (index 37; value, phase, dirty), mask 0. Mean ordinary paid 553234.4638671875. The original #274 identity shell also produces the identical syndrome and dirty-bit corruption at index 37 on two measurement seeds. Phase is not certified there. Quick 108 is not added to the other tests because it overlaps. No official 102400 run or Vercel run.

Initial full 637319 static paid (509732 CCX), retained inverse 559514 (431927 CCX), final 553704 (428217 CCX). Existing #299 317996 is cheaper. This new circuit must not replace the competitive candidate. Lean checks local mathematical identities, not serialized circuit universal correctness. Reproducible sources and exact KMB are delivered in the accompanying chat artifact, not embedded in this repository commit. No score or submission claim.
