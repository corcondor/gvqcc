# Full raw-syndrome direct adjoint with rank-15/guard4 reuse

Research, not a submission. Parent #310, pinned full generator #274/#266 and
component sources #237/#241. This is a new full build, NOT a binary rewrite of
the #310 hash. The existing weighted D,N shell is known to have a fresh
restoration counterexample. Do not promote even if ordinary tests pass.

At each non-anchor leaf use sqrt coordinate ratio p/d. Keep a single GF64
norm and a GF8 norm. Reuse the exact four-product guarded inverse from #241.
Pull both final GF64 rank-15 products through the public linear mask and
materialize a single linear numerator parity at a time; apply CCZ directly,
not a full inverse output. HMR cleanup repays each norm/product with linear
and quadratic phase coefficients. Static synthesis model (11 retained conjunctions, rather than the 7-wire recompute ladder): 11+15+6+4+12+30=78
paid/leaf, 33 scratch (instead of 35). The 70 fixed anchors use #310's
compensation before the raw-key transform, and the same additive FFT
evaluates the classical polynomial alongside the quantum coefficients.
All masks remain classical public data. No fitting to verifier or salt.

Independent JS certificate checked in this conversation: 36 GF64 tensor
basis checks, 16 guard4 truth cases, all 8192 (denominator, guard) pairs,
1,179,648 binary phase coefficients, no mismatches. The Python source
repeats the coefficient check, then performs 16,384 native leaf shots.
Full build and full replay are separate and are NOT yet certified.

Important singular seam: the #274 fused CRT synthesis maps (N,D,P) to
(D,qN+PD). At D mod q=0, if P is nonzero, two words can disappear from
the representation. A unitized inverse in the closing cannot reconstruct
lost information. Guarded synthesis is evaluated on the SAME raw inputs
as a diagnostic, not claimed as a universal repair. A complete repair
needs a reversible encoded residue: store P in R mod q on the singular
branch and apply a projection when interpreting R. Subsequent stages must
carry this encoding; do not insert only a local guard and claim success.
The weighted scan still requires the shell's physical-root/magnitude
contract; the general quotient-remainder theorem is not proved for this
compiled shell. Strict replay includes all weights, zero/onehot/dense masks,
high valuation, fresh distribution, saves every failing input and separates
identity shell failures. Cost model is not measured mean or a Kaggle score.
No main merge, no submission.
