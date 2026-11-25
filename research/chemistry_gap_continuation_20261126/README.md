# Gap continuation: numeric PASS, NOT SUBMISSION
Parent PR150. Executed CPU whitened factor fitting, fixed-W offset SLSQP, code-preserving H1 updates, exact scalar gap retraction, gap continuation and orthogonal L1 gauge optimization.

| Checkpoint | e1 (mHa) | e2 (mHa) | lambda_eff | gap (Ha) |
|---|---:|---:|---:|---:|
| PR150 gauge_h1 |19.930143842|20.056430640|47.239021976|3.9148981|
| Phase I (35 loss/grad evaluations, best feasible) |19.997657294|19.997343212|47.826029080|4.012773248|
| Offset + H1 repair + second offset |19.999000003|19.997343212|47.782485974|4.005185217|
| Gap 3.98, gauge |19.995000207|19.995000218|47.612502121|3.98|
| Gap 3.95 (best, very small e2 slack) |19.999004218|19.999994565|47.471717371|3.95|
| **Selected gap 3.952 + gauge** |19.997066853|19.998842336|47.451952970|3.952|

Independent packed FeMoCo numeric PASS. Selected Lambda=286.8555344933977; SHA256 ecf53db581a5f0385a93ce221e844a19b4a9e1a97a8d0939e30ab4402d333f3f. Complete 16-address-block bit0, bit5 XOR bit6 and bank 8/10/13/14 rank4 invariant checks PASS. 1186 angle words differ from incumbent (155 vs PR150). Not native compiled. Fixed T13214/Q405 conditional cost 253947193.15 vs incumbent 251089991.59; at least 75 CCX/pass reduction required to beat incumbent assuming all else unchanged and two loader passes. Hypothetical bank10 saving alone insufficient.

Exact gap transport: for each block alpha=Wz, P=alpha*z^T/||z||^2, set z'=tz and W'=W+(1/t-1)P. Then W'z'=alpha. If g0 is gap excluding 0.5*sum ||z||², t=sqrt(2*(g_target-g0)/sum ||z||²), with positive radicand and nonzero block norms. This permits a coupled gap and moment parameterization. Analytic error derivatives finite-difference checked; lambda subgradient crosses nonsmooth L1 zeros, so no universal smooth-gradient claim. Direct floor-target fit still fails, best e2 20.024877563 mHa at 3.914899. Unbounded score-weighted ALM diverged, rejected. No new Lean execution, native verification or official score; no main/Kaggle change.

Repro archive GVQCC_Chemistry_GapContinuation_NOT_SUBMISSION.zip, 67 entries, SHA256 8c5301f0630b64ddd2cf03815f69820a2aed2b3fd40945912a7a56ab5a820188, actual training scripts, source dependencies, packed reference, checkpoints/logs and independent receipts. Supplied in research conversation. Do NOT combine changed angle table with incumbent KMBs.
