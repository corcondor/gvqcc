# DQI phase seam: product windows and split projective normalization

These are exact KMB component tests on the physical #261 seam map, not a replacement full DQI tape. The missing component is still a native in-place reversible half-coordinate adapter, including the inverse of (Amod B). There is no Kaggle score or submission from these experiments.

## Corrected normalization

Do not rescale every numerator coefficient. With raw factor (s=D_{35}
e0), inverse Frobenius gives (A_{raw}=uA), (P_{raw}=uP), (Q_{raw}=uQ) with (u=sqrt{s}). In the quotient by monic (B), the same factor cancels:
((uA)^{-1}(uP)=A^{-1}P), likewise for (Q).
Normalize the 17 non-leading odd D words (B) first; use raw A and raw lower N at the adapter, leave raw N34 intact; only then normalize the 18 even D words and N34. Apply inverse Frobenius to the normalized N34 separately when placing it in the H leading slot. The normalized leading D word is implicit 1; the raw leading word retains the scale for restoration. Reverse this order after the phase scan.

- Full #261 paired normalization: **6,144 CCX/paid**, with a 12-bit inverse live across its middle.
- Split version: **3,816 CCX/paid**, 63,234 instructions, 900Q allocation probe, 2,560/2,560 KickMix shots with identical output, phase, spectators and clean scratch. Allocates all 35 free lines where the adapter should run, and 11 separate lines at the phase slot while sharing the inverse across the phase. These slots currently run identity probes, not the adapter or phase itself. Across all nine normalization checks, 23,040 shots passed. The scale-cancellation arithmetic separately matched in 256/256 coprime cases.
- The measured raw-key pair (220,343), spectral phase (65,457), and split normalizer (3,816) sum to 289,616 static paid, leaving a **nominal** 26,384 static units before the 316,000 reference. These disjoint counts add no evidence of a full-circuit cost or score.

## Existing coefficient words as basis-change frames

Reuse the #246 field multiplier and the spectral rank-one transport on actual seam wires. For each fixed evaluation point, make the operand values available through reversible changes of basis within each control block; temporarily conjugate the output block so that one *dirty* target word implements the interpolation column. Pay back the shear using the updated target word. No operand or product scratch word is added. The tests seed **all 900 lines**, including other coordinates and unallocated spectators, with arbitrary values and verify the requested XOR plus all spectator values and phase.

All eight KMBs passed 512/512 per window, 4,096 total. CCX, static paid and measured paid agree:
- Low and high product windows separately: 1,428 each for sector 0 and 1,386 each for sector 1.
- Reversed quotient windows: 1,386 and 1,302.
- Low reduction windows: 1,386 and 1,344. The known monic term is outside the low window; the two sector lengths are 17 and 16.

One *arithmetic* pass would cost 8,232 CCX if each full product could share its low and high targets in a single pass (196 field products rather than 198). The windows actually tested execute low and high independently and sum to 11,046 CCX. Neither figure prices the live storage of both products/quotients, the unknown Bézout inverse (A^{-1}mod B), calculation/lifetime of the reversed modulus reciprocal, nor erasure of the old numerator after an in-place change of coordinates. In particular, the low and high product coupons reuse coordinates that are still occupied in the full conversion; they cannot be composed as-is.

## Reproduction

Run the pinned #246 generator to obtain `half_magnitude.cpp` (see PR #246, head `f88814465d71ec05d9585efb78a7da1aca560e8d`). Here, set `HALF_SOURCE` to that file. The normalization uses `research/dqi316k_joint_crt` at #261 head `bf87158c58b5f183f08798d6d449e42c10177019`; set `PYTHONPATH` to include that directory and install KickMix 1.0.0. Run the following in a writable copy of this directory with the original sibling paths:

```sh
ln -s ../phase261/raw_audit.json raw_audit.json
python emit_windows.py "$HALF_SOURCE" ../phase_spectral/quotient_spectral.cpp.inc raw_audit.json
g++ -O3 -std=c++17 windows.cpp -o windows
for k in low high revq red; do
  for i in 0 1; do ./windows "$k" "$i" "$k$i.kmb"; done
done
python verify_windows.py
python normalize_release.py
python split_half_algebra.py
lean -DwarningAsError=true WindowTransport.lean
```

The four new local Lean lemmas, the five physical pivot lemmas, the three raw phase seam lemmas and the three spectral middle lemmas were checked with Lean 4.35.0, warnings as errors. These are local algebra and indexing proofs, not a proof of the full DQI tape.
