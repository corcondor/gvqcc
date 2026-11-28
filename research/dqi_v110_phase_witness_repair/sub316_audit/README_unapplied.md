# Full 8-anchor DQI: what is and is not ported

Pinned tape SHA256 24e9d894b98af548cd22fb7ab82f12a1b7034b81a5ddbddc03571626e48d0ea0.
Common-input mean 316119.02546875 at 900Q on 102400 shots, zero observed
ordinary errors. Target <316000: more than 119.02546875 executed paid
gates to remove. No new paid reduction or full-oracle claim here.

## 316.09k clarification

#299 reports 316094.017578125 executed gates on 1024 native KickMix shots.
The exact same #299 Joint SHA a8b5c62e… measured 316126.430752 on #306's
102400-shot panel and 316124.943555 on our common panel. Within that panel,
100 disjoint 1024-shot subsets span 316078.679 to 316167.062 (#299), and
316072.985 to 316160.992 (8-anchor). Small subsets are not alternate circuits.
#8 remains the lowest-cost verified full tape in the matched 102400 comparison.
No <316000 complete result found in accessible receipts. #307-309 are scans,
a new phase-only component, and reproductions, not a lower complete oracle.

## Prior results not in the complete 8-anchor

1. #308 / #301: direct mask observer and confluent adjoint. #308 native
   kernels 1008→0 and 2184→0 under degree bound and phase-only use with a
   classical output mask. Does not replace a live quantum product. Re-ran
   #308 on exact 8-anchor: 1,136,187 affine/dual blocks and 317,888 CCX/CCZ
   sites, zero matches. New scans on 310,835 unconditional-within-scope CCX
   sites found no delayed HMR cut or phase sandwich; not a lower bound.
   Need to lower the product consumer together with the product.
2. #296: shared dirty echo 592→234 locally with synthetic payload.
   Mapped #294 cut 57,227,861 to #8 cut 128,428,359 by unique 256-opcode and
   quantum operand window plus 256 paid operands (classical IDs omitted).
   Ran the actual #8 KMB prefix in KickMix on 622 archive inputs. 495 exact
   outer supports via the scale-2 frame, 127 lost every true root. Forney
   recovers the correct amplitudes on 495 in reference arithmetic. A projector
   cannot recreate roots, and the native target/payload ABI is not identified.
   This is not a 358-CCX drop-in substitution.
3. #302 / #304 with #298/#299/#309: measured Schur raw-S alternate prefix
   285708→285150 and 285708→281705, respectively, from the same baseline.
   #304 retains 60 higher-confluent failures. Savings are not additive
   without a fresh joint measurement. #309 reproduces converter-only numbers.
   No actual native 900Q raw-S→phase→restore graft to the cheap return.
4. #300 / #303: adaptive half-GCD and packed division/reciprocal as native
   components, not a whole KMB. Peak 142 words in naive full recursion;
   no full restoration and phase continuity. #305/#307 instruction-only
   affine/liveness transfer does not demonstrate a paid saving.

## Hot-path budget on the actual 8-anchor tape

Ran the #306-transfer extract_blocks/export99/probe99 tools with two
ordinary batches. 333 windows of 99 CCX, 330 active on all observed 1024
lanes, average 331.4736 activations. 665 of 666 window-batches have ranks
(24,24,48,49 including constant). The lone lower rank at 121020556 reaches
full rank in the other batch. No common affine dimension reduction in
these windows. One exact CCX cut at 120 of the fully active windows would
cross the threshold at the observed activation frequency. This is a
budget, not an achieved reduction.

## Reproduction

map_exact.cpp and map_phase_loc.cpp need ../other/src/native.hpp from the
8-anchor source archive. Build with g++ -O3 -std=c++17, then use
./map_exact ../d294.kmb ../d8.kmb 57227861. It returns the two bounding ops.
deferred.cpp and sandwich.cpp are scan tools; edit emission branches were
not exercised. Use prefix.cpp and native_prefix.py from the earlier
ghost_scale2 source and #296 archive. Compile prefix.cpp with the prior
joint_work/audit/common.hpp; use ./prefix ../d8.kmb before.kmb 128428359 and
python3.12 native_prefix.py before.kmb ../joint_work/audit/saved.bin d8capture.bin.
Use ghost_scale2 diagnose.py and, from seam, run
PYTHONPATH=.:.. python ../audit_eight_locator.py. No captured inputs published.
