# Packed continuant / Frobenius native solve

Research only. Base #326. No submission or merge. The two-RHS quotient solver and polynomial reciprocal are fixed Euclidean degree-profile circuits, not coherent all-degree dispatch.

- Use #326 half-degree Frobenius identity and two-RHS return; #303 packed division to retain quotient in retired coefficients; #284 transposed Toeplitz and interpolation for triangular return; #287 shared reciprocal; #293/#302 HMR phase repayment of an old field word from the product and its inverse scalar. No additional polynomial bank.
- New continuant inversion: if M=product [[q_i,1],[1,0]], (B,A)=g(M00,M10), det M=1. Reversing quotient order transposes M. Alternating g^2 and g^-2 quotient scaling, with terminal g inverted if the quotient count is odd, reconstructs B and A^-1 mod B in place. 1024 independently executed arithmetic cases exact. Native compiler recycles quotient slots and zero gap slots.
- Packed two-RHS Euclid lift: B=qA+R, C=kA+c, c=Rt+As implies C=A(k+qt+s)+Bt in characteristic two. Use the packed remainder and quotient as the truncated Laurent series of B/A, apply upper-triangular updates and restore the source coefficients.
- KMB forward/inverse, scratch, and phase tests are defined for five fixed profiles including two degree-17 charts. Report actual CI results, not estimates. Scalar inverse assumes nonzero leading pivots; fixed degree profile must be valid. Neither full raw-S nor #314 native replacement is claimed.
- Baseline remains 316094.00 on its matched 1024 shots. The latest whole-tape data is unavailable to the local execution service (ClientError). No change to score or original submission artifact.
