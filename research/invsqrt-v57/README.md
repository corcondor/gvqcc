# V57 — multi-stage carry-free streams and exact interval-tensor exchange
Research only / NOT SUBMISSION. Stacked on PR132. Independent of PR135–137; no arithmetic addition across lineages. Archive GVQCC_V57_CarryFreeIntervalTensor_NOT_SUBMISSION.zip (245863 bytes, SHA256 4f8a38c3b8b217298283553c3ff574fac44ca7d8944e937af2bc738eb107bb20) includes complete source, original parser/template, actual KMBs, explicit readout ABI, receipts, scripts and SHA manifest. Archive available in research conversation. All new native circuits are PARTIAL, not full competitive oracles. No official verifier/score/main/Kaggle changes.

## Actual native results
All independently reread serialized KMBs: legal x=1..3133452, weighted readout equivalence, input/work restoration and all independent HMR phase coefficients checked. Expected paid = CCX + 1/2 independently HMR-conditioned CCZ; excludes downstream consumer and rotation synthesis.

| first V55 retained product | Q | CCX | guarded CCZ | E_paid | ops | weighted outputs |
|---|---:|---:|---:|---:|---:|---:|
| PR132 baseline |36|6998|see PR132|not compared|19268|57|
| measured prefix counter |34|2222|404|2424|24288|57|
| chunked prefix |32|2058|408|2262|23384|73|
| 3:2 compression |32|1593|408|1797|21740|101|
| row stream |30|376|31|391.5|2216|143|
| exclusive support stream |31|372|31|387.5|2142|105|

Q34 SHA ac78bc8f6c552c81ff5d120ada0c24e6593295cc984d5937852797b0884288af; Q31 SHA 06f3f42ae673ae5604755a6d01872343b7b32cbc1f47b23a3f66d676a55a5b59. 24 address care set affine-flat dictionary: 1281 unique atoms degree 2/3/4, 121780 pair quotient states, at most 4 atoms plus affine remainder. Exact 13-row global partition for exclusive-support coloring, 105 outputs within specified family. No universal optimum. Different snapshot ABIs must not be compared as whole-circuit cost. Q36 counter built but replay timed out; not included or claimed verified.

## Two-stage native contraction
Signed weighted stream C2 + C3*t/2^17 + C4*t^2/2^34, individual binary terms truncated at guard g. Hold c_i*t_j over every t_k consumer; t^2 symmetry doubles off-diagonal terms. Actual Q30 g0: 1237 CCX+83 guarded CCZ=1278.5 expected paid, 8614 ops, 742 snapshots, 1037 independent HMR, SHA 0834bc10c1a5364ef0a81b7bb8d9959924ab5461d8571f01aebd373ce279aa92. Q30 g2: 1437+83, E1478.5, 9414 ops, 932 snapshots, 1237 independent HMR, SHA 1b61ce8d4bc7b4cf533c8f3e0a7c34ce89dd1b8a5735cbf08ba5bd76643cef95. All legal controls verified. No canonical intermediate word; remaining two Horner stages tested classically (not emitted): guards 0..6 all integer analytic tolerance PASS, g0 absolute margin 21268887, g2 42621882. Different approximation from original V55. Main obstacle: consuming this stream without repeated computation, final weighted phase aggregation.

## Full polynomial model and interval tensor
Exact multilinear finite differences of V55 quartic at 17 offset bits; final round once to 34-bit phase code (F38 internal). 384 terms pass, 9216 nonzero coefficients/8985 distinct per-atom weights/50671 binary weight count, margin 68193993. Intersect allowed integer value intervals across all exponents at 2350089 normalized care points. Exact coordinate minimum distinct nonzero coefficient values via interval stabbing. Without reserve: 309 atoms/4389 coefficients/3321 distinct weights/16024 binary weights, margin 190680. With minimum reserve 50000000: 323/4669/3575/17138, then 180 adjacent support pair exchanges, 70 adopted, ->315/4642/3552/17014, margin 50014667. Independent full integer zeta replay, legal 3133452, zero violations. Final phase code SHA a138845a4b6522a9a98c773b91a7feebe6746c0c8aa507120ebcfaaf162b2777. Specification only; distinct weights are not native rotation count, and 31 generic rotations presuppose low-cost canonical phase-bit production. No complete native polynomial oracle.

## Literature
Gossett arXiv:quant-ph/9808061, Luongo et al. arXiv:2407.20167, Halpenny/Sireesh/Wallden arXiv:2611.26605, Sun et al. arXiv:2409.04587. Bounded carry-save streaming, measured erasure, in-place/weighted phase alternatives; no claim of directly porting complete papers. OpenAI Fourier Nov24 2026 build/repair.tex, matrix exponent nine-fourths build/shaving.tex: predictor and simultaneous correction, trivalent compression and shared contractions. Actual algorithm is finite integer subset zeta, coefficient interval stabbing, and Boolean product sharing. Not an asymptotic algorithm port or quantum gate bound. Local Lean proves algebraic identities only; full native replay separately. All #118 acceptance conditions remain open. 
