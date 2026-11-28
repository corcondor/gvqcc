# Packed evaluation-gauge Schur + Toeplitz integration

Stacked on #269 (working lineage #266). Research only; no submission or main merge.
The original 316K donor is not replaced, nor claimed repaired.

- #245/#248/#265/#269: Schur elimination with scalar and alternating pair pivots, normalized retired source pairs, two RHS sharing all source transformations. No bound on Euclidean degree gaps, for coprime A,B. One clean field word for interpolation; 71 words including the implicit monic sentinel and both 17-word RHS, plus one P top word for the D,N to D,H ABI. The 35-bit history is a combinatorial bound, not a synthesized coherent controller.
- #267/#213: cyclic middle-product tensor for the final Toeplitz shear, shared live affine frames and reconstructed 42-product GF4096 multiplier. Its binary CNOT/CCX basis certificate (144 product + 12 dirty target lanes) is checked in the local Python implementation.
- Same unit-gap degree 17 case: previous Laurent tape 3568 mulxor, 186 inverse scales, 424 scales; new 1278 mulxor, 153 inverse scales, 85 scales. Nonlinear words 4178 -> 1516. Constant linear work increases, and actual controlled scales are not yet lowered.
- Local test: 297 arbitrary coprime pairs, 1188 RHS checks, 2545 scalar and 288 pair pivots, all exact forward and reverse. Separate synthetic weighted D,N -> D,H test: 360 cases across weights 0..35, 6300 physical roots and 360 phases, zero errors; mean nonlinear words 3896.8556 -> 1533.0. This is not actual donor prefix data, nor a whole-circuit test.
- Hybrid binary check: 9 weighted D,N traces and 1 alternating trace, both directions; 35 constant-twisted rank42 kernels certified. For the 17-scalar-pivot ABI, 54390 CCX forward and 54390 reverse only for lowered multiplication-add gates, 153 ix/85 sx still unresolved per direction (swapped reverse). No full cost or 900Q claim.
- History recurrence T(0)=T(1)=1, T(n)=T(n-1)+2(n-1)T(n-2), T(17)=25330978113 < 2^35. 17034 rank/unrank checks. Nominal bit storage 840+12+12+35=899, excluding coherent dispatch and scale workspace. No native width guarantee.
- Prior #269 strict CI run 46116350096 failed at reserved identifier `by` (two theorem binders); rename to `byy`, add 12 new Lean statements and strict audit. New Lean run must be checked.
- Complete Python source, tests and receipts are delivered in the research conversation ZIP; this PR records local measurements and the Lean source, not the complete Python implementation or KMB.
- Blockers: no local KickMix/Lean, Vercel #269 quota failure and no running sandbox available; raw marker classification, repeated-root input interface, coherent selectors, inverse/scale lowering, physical workspace and official replay remain open.
