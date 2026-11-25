# V54 — conditional multi-output phase synthesis (width is a variable)
Research only / NOT SUBMISSION. Stacked on PR121, independent of PR123–125. No official verifier or competitive score. No complete new low-width oracle; all ten acceptance conditions remain open.

## P0-A/B/C: actual native sparse sub-oracles
Pinned PR92 source SHA256 cf1ba95ab89d6c745f13a0629f8638afd0e3e62b8c8168b6bd9362d8dd130d2b. Rechecked the archived exact ANF: all 8 assignments of relevant private HMR indices 340,358,794 give the same phase on all 3,133,452 legal inputs (not a fresh symbolic extraction). Zero-history masks merge to 39 nonzero weighted roots. Eight selected masks have sparse support or sparse complement restricted to x<65536. Add the previously known quarter-turn pair (roots 2,37) fused into one rare predicate x in {2,3}. Nine rotations, five generic; this is a PARTIAL phase oracle, not the complete invsqrt.

| Width | Joint prefix CCX | Hierarchical CCX | Conditional input lending CCX | Conditional ops |
|---|---:|---:|---:|---:|
|24|34120|—|4618|7727|
|25|32768|9328|3914|6513|
|26|—|—|3494|5701|
|27|31424|6236|2922|4785|
|28|30496|—|2854|4707|
|29|27344|4570|—|—|
|31|—|3060|—|—|
|33|—|2398|—|—|

Each native KMB was reread and exactly checked on all 3,133,452 legal basis inputs, rotation controls, input/work restoration and angle weights. Independent second checker verifies all five conditional circuits and Q24 joint prefix comparator. Q24 conditional SHA256 7a2cd095ff2c8baa747a482d52348d5b2ec7cbc183781028f9c2ebc6be529aa8. No HMR. 86.47% reduction versus same-width joint-prefix comparator, still noncompetitive even for this subset.

Technique: vector XOR labels on a 16-bit prefix trie, dynamic program for joint tags then cache/no-cache/sibling recurrence. Cache upper-zero flag h on a clean wire. The upper six input bits are zero on h=1 and can be borrowed conditionally; gate transfers by h, inverse restores arbitrary dirty values outside the branch. Sibling flag exchange p(!b) XOR p = pb saves recomputation. Dynamic programming is exact only over specified trie and options, not globally optimal.

## P0-B: new 31-generic-rotation mathematical specification
Keep original high weighted Boolean masks. For a cutoff k in exponent of weight magnitude (nearest binary power), replace remaining low roots by m=34-k signed binary coefficients. H(x) is retained phase, r=target-H in signed modular lift, grid d, sign mask A. Choose q in [-A,2^m-1-A], z=q+A; control c_j=bit_j(z) XOR bit_j(A), weight d*2^j*(1-2 bit_j(A)). Sum is exactly d*q. 11 finite grid choices k=20..30: all exact integer tolerance PASS, signed reconstruction independently checked. k=23: 20+11 generic, d=1087888884,A=1987, absolute margin 77434783, worst error/tol=.8753696828. k=30: 27+4 generic, d=1141129404,A=12, margin 50729146, worst ratio .9937591698. Existing 33-root angle-only optimal margin 36584657. Synthesis proxy 239.003911 -> 219.432602 (k23) or 222.080727 (k30), NOT measured official. No new low-generator native implementation.
  
Exact care-fiber criterion: permitted code interval for x is I_x=[ceil((r-tol)/d),floor((r+tol)/d)] intersect representable range. A deterministic shared code on features F exists iff each fiber has max lower <= min upper. Max coverage histogram gives exact minimum failed rows for any function of F under this grid. k30 six old low bits: 56/64 incompatible fibers, 2,742,936 rows in such fibers, at least 57,469 violating rows even with optimal code per fiber. Add input high six bits -> 48,280 minimum; add low six -> 57,269. At 38 captured reachable source frames (parent114 SHA a7f7acca778a02d599bb9f0dfcd774dcc49b002b830d2c331250b9467a3c6beb), at most one of six old low masks is affine in a single frame. Seven late full feature frames distinguish every legal x, so expensive general lookup is possible but not economical. This is a precise restricted-model obstruction, not a lower bound for arbitrary 31-rotation circuits.

## P0-C/D: exact input-specialized observation graph
Versioned XAG, fixed private history; remove ten selected sparse/constant/paired roots. Specialize upper five input bits (24 consecutive ranges covering all legal x). Verify all retained root masks exactly in each range. Formal peak rank distribution: 30:11 ranges; 31:4; 32:3; 33:4; 34:1; 37:1 (x=1..131071). 23/24 ranges <=34; 15/24 <=31. This is formal rank modulo constants, excludes coherent selection/control overhead and is NOT physical width. Separating sparse roots alone does not remove global peak rank37. Do not concatenate branches naively. Focus next on shared normalized-mantissa arithmetic and a low-root correction generator (PR123 dyadic parity collapse), conditional loan and measured uncomputation. PR124/125 22Q diagnostics retain thousands of rotations; no additive merge across parents.

## Literature and proof scope
Khattar & Gidney, Rise of conditionally clean ancillae (arXiv:2407.17966): implemented exact guarded borrowing and dirty restoration on native sparse fragments. Reqomp: cache/erase tradeoff. OpenAI Nov 24 2026 preprints: finite Fourier predictor/residual repair (repair.tex, kernel.tex) and matrix multiplication exponent 9/4 (intro.tex, shaving.tex); used finite predictor residual and multi-output common-factor contraction analogs; neither asymptotic bound is a finite native quantum gate guarantee. No claim to port either general theorem. Local Lean Boolean identities, fiber interval obstruction, signed-code identity; no whole-circuit formal proof. 
Reproduction: GVQCC_V54_ConditionalMultioutput_NOT_SUBMISSION.zip (3,197,197 bytes, SHA256 347358c13e8cb7781e056a4a4e27de84afed3e8e1c786870df407b379ef26ef2), supplied in research conversation. Portable code, source KMBs/archived ANF, native fragments and receipts. No main/Kaggle changes.
