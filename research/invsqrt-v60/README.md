# V60 — cross-mask phase transport and canonical first-stage consumer
Research only, NOT SUBMISSION. Based on PR143 and independent PR141 packed carry donor. No complete invsqrt, no official score, no main/Kaggle changes.

## Actual serialized results
All rows checked on 3,133,452 legal inputs, input/work restoration and all independent HMR phase coefficients.
Same PR143 two-stage intermediate: Q36 E1342/577 rotations -> E1551.5/457 rotations (1512 CCX + 79 guarded CCZ, 10703 ops, 1200 HMR). Fixed partial proxy E+7.25R 5525.25 -> 4864.75. Q34 E1389/577 -> E1630/492, proxy 5572.25 -> 5197.0. Target integer phase SHA e4a7a79b75dbca5f375f48fb94ab52e3da0e987ca4b773844223d64b18041292. 52 common-pivot batches, 32 other exclusive merges, 57 same-mask triples, 40 cross-mask triples at Q36. Finite group search with nonmonotone exchanges, not global optimality.

Independent PR141 model repaired_k12 (not the two-stage phase target): normalized first Horner value v3/32 = C3/32 + floor((2*m*T+m+8)/16). Every following circuit includes normalization, product, coefficient handling, intermediate phase and restoration. Target signed integer SHA 1c05552f7be2b134e85c73d91903cb038c68043e8e76d70984ff89a900462408.
| Q | construction | expected paid | rotations | ops |
|---:|---|---:|---:|---:|
|36|initial canonical|1078|30|see archive|
|36|carry-init + exact care replacement|561|30|4525|
|35|recursive increment + exact care replacement|567|30|4539|
|34|recursive increment + exact care replacement|621|30|4544|
|34|redundant integer phase + exact care replacement|516|31|4339|
|36|borrow pebble, full coefficient dictionary|1158.5|17|11949|
|36|borrow pebble, 10 active address care set + exact replacements|811.5|17|7424|
Use P'=m*T+floor(m/2), q=floor((P'+4)/8)=(P'>>3)+P'_2. Initial carry absorbs midpoint. For q bit generation, HMR erase and hierarchical increment avoid large controls. For the 17 rotation route subtract q from abs(C3/32) via reversible borrow pebbling: 4 pebble slots, 32 forward toggles and 32 reverse; exact synthesis of coefficient bits on the 10 nonzero m segments when only used to generate a borrow, full coefficient function for phase readout. On inactive segments q=0 and all borrows remain zero. Exact reachable affine replacements rechecked after serialization. The 17-rotation route is NOT the cheapest proxy point. Q34 E516/31 is the best first-stage width-times-fixed-proxy point of these routes, not an official score. Intermediate phase operations are diagnostic; a complete arithmetic oracle must consume live digits in subsequent stages rather than summing independent intermediate phases. PR143 and PR141 targets differ and must not be combined by adding their costs.

Literature: Gidney arXiv:2507.23079 (constant-workspace classical-quantum adder); Gidney arXiv:1709.06648 (measurement AND erasure); Halpenny et al. arXiv:2611.26605 (in-place arithmetic, Fourier basis not directly portable); Amy/Lunderville relational analyses (reachable affine care); AlphaTensor Quantum (Hamming-weight phasing). Finite shared-factor / grouped phase contraction ideas, not entire paper implementations. Local Lean source and portable finite checker provided. Full native source, exact KMBs, receipts, source dependencies and replay commands in companion archive GVQCC_V60_PhaseDigitTransport_NOT_SUBMISSION.zip. 
At Q36 E1551.5, even optimistic official rotation synthesis at maximum possible min-margin 621138291 gives at most 21 generic rotations before other stages. 457 is not competitive. Remaining stages and final phase generation are NOT emitted. No official verifier or score update.
