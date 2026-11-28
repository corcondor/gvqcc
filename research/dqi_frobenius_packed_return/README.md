# Frobenius packed Schur return (research only)

Pinned #323 lineage, 316094.000 matched 1024-shot DQI. Do not replace the full candidate based on component counts.

## Actual algebraic composition of prior work

- #296 ghost splitting and #287 norm retention: split P=A²+XB², H=gcd(A,B). From uA+vB=H obtain B²(Xu²+v²)+u²P=H². For square ghosts with no physical-root multiplicities, N divisible by H². Q=P/H², n=N/H². Then V=n(Xu²+v²) mod Q solves Q'V=n. This is one half-degree Bezout, not a full-degree inverse followed by ghost cleanup. If a true root is missing, recurrence fails; never claim this repairs an invalid P.
- #299/#304 shared two RHS: after canceling H, write n=C²+XD², V=E²+XF², T=G²+XJ². n=B²V+QT iff C=BE+AG+XBJ and D=BF+AJ+BG. Compute G=(A^-1 C) mod B and J=(A^-1 D) mod B from one inverse cache, then E=(C+AG)/B+XJ, F=(D+AJ)/B+G. #300/#303 packed division and variable degree handling are the intended front end; only the return described below is physically compiled here.
- #284 transposed middle product: for monic B of degree m, t=rev_m(A)/rev_m(B) mod X^m, T(G)_i=sum_{j>=i} t_{j-i}G_j. c is the scalar quotient of C by B. Then E_0=c+T(G)_0, E_{i+1}=J_i+T(G)_{i+1}, F_i=G_i+T(J)_i. Store E_0 on c, E_{i+1} on J_i, F_i on G_i. Process low degrees first. Cross-block Hankel updates use transposed interpolation of a product of lengths l,h with l+h-1 field products instead of lh. Use the #300 packing invariant and #303 triangular inverse idea to temporarily turn reversed A coefficients into t and undo; no ancillary register and no HMR changes. #309/#187 exact 42-CCX field multiplier reused with independent full ANF check.
- #301/#308 dual phase: V is evaluated only at physical points; phase Tr(e*m) can be contracted without explicit magnitude on the artificial roots. This is an interface contract, not a graft to #323.

## Test scope

Independent finite-field reference over GF(4096), 1080 synthetic inputs weights0..35, three types (unpadded, simple irreducible quadratics, repeated irreducible quadratics), 18900 root-amplitude checks, 1050 missing-root and 1050 repeated-physical-root rejection checks. Cost counts use one-pass EEA for baseline (no redundant initial GCD), schoolbook coefficient products, and per-divisor reciprocal cache. They are not native paid estimates.

Native fixed-odd-degree return accepts arbitrary A,B,G,J,c words. At m=17, width 840Q, not including any other decoder state beyond these 70 words. Scalar return needs 2m²=578 field multiply-adds (24276 CCX). DP block schedule d(17)=54 gives 4d(17)+2m=250 field multiply-adds (10500 CCX). This cost is checked in generator and CI; claim actual native values only after successful run. It does NOT include generating the half-degree inverse or G,J from raw syndrome. No all-domain decoder proof or full score claim.

Full #314/#323 live tape is not accessible in this local compute session (ClientError); no raw-S splice. Current best DQI remains 316094.000 on matched 1024. Known stress failures not repaired. No main merge or submission.
