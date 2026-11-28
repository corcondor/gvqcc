# Native packed half-GCD research results

No full DQI splice or score claim. The classical joint half-GCD predecessor passes 1440 legal inputs; physical recursion with coherent degree dispatch remains unfinished.

## Joint interpolation with rolling in-place evaluations
Fixed degree bound on the sum, arbitrary dirty target, preserved input banks; 384 shots per binary.
| (a,b,c,d,k) | Old Q | New Q | CCX | Old ops | New ops |
|---|---:|---:|---:|---:|---:|
|2,9,3,8,6|408|384|504|22349|19519|
|4,18,5,17,13|804|780|1092|103387|77681|
|3,18,4,17,14|768|744|1176|110982|83866|

## Native packed division, including HMR and shared reciprocal
Input A capacity n+1 and B capacity m+1; B[m]!=0. A low m coefficients overwritten with R, high n-m+1 with Q. B unchanged. Explicit inverse emitted. One 30Q inverse/scale workspace. No host selection.
|n,m|Q|old paid|new paid|old ops|new ops|forward new SHA256|
|---|---:|---:|---:|---:|---:|---|
|35,33|870|4386|2370|92315|91144|426e325b2787627a20394719fa92ed78c308e2fbd69fb2fd04f9ca1c66b65088|
|35,22|738|13626|7410|289501|289464|ac71afc7d3d972c35f92bb6bbb3d4277ea67c651d7c27ac2d20c7fdf60620df4|
|35,17|678|14466|10518|310491|309795|47ddf9cce3b8b065eeaebef59208a85882e1f13f66c45501fe10c380a8882458|
|52,17|882|27318|23370|586061|585365|7655232e341972cfc2b41e98e57f4dfebe090bf6983721a8a67d5592adc25be1|

384 matched forward and inverse shots per binary pair, independent seeds, zero value/workspace/raw phase errors. Includes zero numerator and exact zero remainders. All six bicriteria truncated product candidates also reduce static CCX and total operations at unchanged width.

Remaining: 70-moment raw-S storage (the two-polynomial explicit top recursion can exceed 900Q), coherent zero-pivot degree dispatch, complete phase scan, inverse and full native verification. Cannot add local savings to #294's full-tape totals. No private salt, submission, main merge or new leaderboard score.

Companion source/KMB receipt archive delivered in conversation.