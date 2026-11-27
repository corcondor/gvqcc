# Fused Hankel/jet/orbit and canonical tag recovery — NOT SUBMISSION

Pinned full donor SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52. Reuse the original PR227 padding/jet theory and PR231 invariant-pad theory. All new measurements below are native KickMix 1.0.0 **local** circuits, not a repaired full DQI. Supplied canonical state is not yet identified in the physical donor.

## Joint coordinates
Root-free F of degree 18 from nine quadratic factors; evaluated nonzero on all 4096 base elements. 52 filtered moments T are invariant under S+tP and the rectangular Hankel rank is min(w,18); exact finite-field rank checked on 962 legal inputs. The two extension jets give four field-word independent linear coordinates on the remaining 18-word prefix. Native 840Q frame and inverse each 2180 clean shots, 0 paid. Factoring F and normalizing along one nonzero pad coordinate gives 69 invariant words and one translating word: 840Q, 64690 ops, 0 paid, 2012 clean native shots. Fixed scale-1 pad changes 426 original bits, 25 in normalized jet coordinates, 8 in the single-word orbit basis. No claim that this reduces whole-DQI Q or that the rank guard is free.

## Shared HMR forward, matched erase, and roundtrip
All three alternatives share the factorized coordinate frame and the first two Hermite chart test. Second test only matters if first residual is zero, so its quadratic part is replaced with the affine difference. Measurement debt is repaid with classical-conditioned Clifford phases.

|Q|forward paid|reverse paid|roundtrip paid|forward ops|shots per direction/roundtrip|
|---|---|---|---|---|---|
|888|173|172|345|137496|2012|
|866|309|308|617|142662|2012|
|855|468|468|936|142711|2012|

All 18108 native shots clean. 1006 distinct inputs, choice counts 982/12/12 including forced first/second pole cases. Forward expects clean tag; reverse expects matching tag. Not arbitrary dirty XOR. No all-later-pole guarantee. Forward hashes respectively 5288cd0fba554f8924e0388c5829007f551dcff41f57e2e093186ac7181077e6, bc05337925911d415974364508ca7a37460f271db6d0387451b89f686c0adc51, 8dc96ab553cd5fc1726e1a78336b9c7b3827cb5bb8bbc6e0606cee4c28c90179.

## Supplied canonical scale recovery
If the monic locator D has a fixed extension root z with fixed amplitude e != 0, the magnitude interpolant V(z)=t*e. Recover scale by fixed linear evaluation and multiplication by e^-1; if D(z)!=0 output zero. The actual local XOR circuits:
- known padded ABI 842Q/0 paid/828 ops, 432 shots clean;
- conditional HMR guard 865Q/25 paid/9665 ops, 1232 shots clean;
- conditional dirty-loan 843Q/178 paid/9772 ops, 1232 shots clean.
Independent interpolation over GF(2^24), 360 legal and 256 arbitrary canonical inputs. Arbitrary initial output tags tested. Need physical donor seam mapping before integration; cannot infer it from an abstract ABI.

## Full donor constant-quotient pass (separate)
18 CCX and 2 CCZ removed, full 900Q tape 69782168 ops, 318952 static paid, hash 0757f9b8588946a143610160a34f6318728fa264ad56afe5a1c2154af6f580c5. Host-selected all-chart diagnostic 1444/1444 clean, mean paid 316092.46468144044 unchanged. Does not repair the oracle; the removed gates were not executed on these cases.

## Evidence and next step
Native generators, dependencies, tests, receipts and local KMB binaries in conversation archive GVQCC_316K_Fused_Orbit_Canonical_Research_NOT_SUBMISSION.zip (SHA256 6e88a5a95634e777bbb512d26115d4a8cf5bcb5c35b605fa9443aacf5bd72877). Core canonical generator in this directory. Lean InvariantPad.lean extends PR231 with Hankel kernel, orbit, conditional affine test and canonical scale laws. Prior SharedChart strict CI success 46065981784; new strict CI 46067025864 must be checked before claiming success. No full-DQI splice, official score, or submission. Need actual donor seam, later-chart totality, high-weight rotation, HMR phase and full official validation.
