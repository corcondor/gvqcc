# #262 official phase failure — exact witness and homogeneous reconstruction

**Rejected for submission.** No repaired native circuit or improved cost is claimed.

Official seed reproduced: 102400 shots, batch 157 lane 244, weight 32, exactly one phase error, mean paid 412884.1909667969. The same syndrome, mask and seed fail #249, #259 and #262. Replaying the same syndrome using three measurement seeds gives deterministic errors for nonzero masks (0/64 zero-mask, 38/64 one-hot, 64/64 original-mask, 30/64 random dense). No restoration error. This is inherited, not a newly introduced rounding error.

The actual extracted heads and two terminal field words are archived in extract_witness.json. The implicit monic synthesized locator on this input has no nonzero field roots. The first thirteen ordinary continued-fraction heads agree with independent exact GF(4096) calculations. Head index 13 (zero-based) has q=X²+X+2140, numerator residue [2086,2864], denominator residue [0,0]. This is an interior pole, not termination.

At this pole use h=0 and the uncancelled homogeneous transition (N,D) -> (qD,N), rather than a finite quotient or termination padding. On regular charts use (D,(N+hD)/q). The fraction-free backward transformation (U,V) -> (hU+qV,U) is the inverse up to a common factor in characteristic two. All 34 extracted heads and both terminal words match on this witness. The reconstructed numerator and locator equal the original rational pair times q; all 32 support roots and all magnitudes agree, and the remaining 4063 field points have zero magnitude. The extra factor has no field root and cancels in the residue formula. This is a reference computation on the captured input, not a quantum gate-level certificate.

Run homogeneous262.py with the exact crt882 module from the original Vercel experiment and the adjacent JSON files. capture262.py and replay_captured.py preserve the original Vercel paths and need the original native files and official verifier. The full original verifier seed is deterministically reconstructed, not selected for scoring. The other audit scripts' environment is not standalone. The native synthesis stage still needs a total reversible homogeneous treatment, including multiple interior poles, terminal degree variations, width and phase compensation. The added Lean file proves general algebraic lemmas, not native refinement. CI must pass before claiming even those lemmas verified.

Existing #262 cost target (<316000 paid gates, <=900Q, zero errors) remains unmet.
