# Native cutoff-zero boundary diagnosis

All native runs used Vercel sandbox sbx_0hXxFBGiXxlH0xH8ifMruaDvpmtp, KickMix 1.0.0, pinned public source revision a9effc375527bf0b6962c178530d353eb70a3fcb. The modified public v7 pipeline is **not** the frozen 316K KMB. No submission or score claim.

- Full public kv_unfused5 baseline: 900Q, 457849 static paid, 996/996 exact, stress mean 374490.921686747.
- j_min=3: 889Q, 385395 static paid, 18 value, 6 phase errors in 108 shots.
- j_min=0 (generic extraction, unguarded CRT): 889Q, 386704 static paid, 153 value, 83 phase, 153 dirty errors in 996 shots.
- j_min=0 with all CRT stages guarded: 890Q, 387418 static paid, 153 value, 72 phase, 153 dirty errors in 996 shots. 1024 distribution samples happen to pass, mean 386244.8671875; not an official score.
- Guarded key prefix + inverse only, no outer or phase: 890Q, 220343 static paid, all 332 zero-mask shots exact.
- Raw guarded key prefix without adaptive gauge: one random syndrome per weight 0..35, all 36 locator root sets exact, all 36 denominator leading coefficients nonzero; gcd degree exactly 35-w for all 36. These independent diagnostic runs do NOT prove numerator/residue correctness or universal behavior. See key-prefix-roots.json and key-prefix-gcd.json.

## Interpretation

The raw key prefix produces a degree-35 padded locator, not a coprime rational pair. Its common factor has degree 35-w in every observed case. The current transpose14_core.py explicitly assumes coprime inputs and excludes larger degree drops. Thus the paired roundtrip can pass while its composition with that outer stage fails. The domain mismatch is concrete; determining the exact failing operation in the gauge-enabled full tape requires further testing.

A compatible rational path must preserve D=G*d, N=G*n without assuming gcd(D,N)=1. At a simple physical root a of d where G(a) != 0, D'(a)=G(a)d'(a) and N(a)/D'(a)=n(a)/d'(a). In characteristic two use the derivative of the actual padded D, with the existing fixed syndrome-coordinate weights and mask map verified against the direct reference. Keep the padding for reversibility, or use a reversible quotient/degree chart (existing adaptive projective/half-Bezout work), not an irreversible gcd erase. Zero derivative and zero numerator cases require explicit guards. This is the next interface to implement, not a claimed finished circuit.

The acceptance gate remains the exact native complete syndrome-to-phase-to-syndrome tape with all four errors zero across forced, adversarial, random, and historical regression inputs, <=900Q, and mean paid below the intended 316K baseline under matching conditions. None of the modified public v7 candidates meets this gate.
