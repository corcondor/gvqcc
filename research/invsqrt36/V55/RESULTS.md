# V55 — persistent rotation transport (NOT SUBMISSION)

Status: partial 36Q window only; full candidate 37Q, rejected for competition. No official verifier or score claim.

Pinned source SHA256 cf1ba95ab89d6c745f13a0629f8638afd0e3e62b8c8168b6bd9362d8dd130d2b (51317 ops, 1598 static paid, 55 parameterized rotations).
V54 #126 increased parameterized rotations 55->81 for a 36-slot replacement of [14372,14516) and subsequent swap. V55 restores the original 55 rotations, including exact original control functions and angle bytes. It is not a successful complete width reduction.

## Results

- Sample temporal search: 26274 distinct effective cuts, 925 sampled affine relocation matches, zero accepted under full-domain BDD. Do not reuse sampled matches as proof.
- Rare first rotation (source index 25, operation 14387): exactly relocate to cut 159, using existing dyadic range flags and five clean slots. Preserve intermediate products until after rotation: 61->35 ops, 24->14 static paid. Fragment SHA256 18b525a4d3a306699c14fe9be2d74db062bd05694abe719581fcfd909a091e22.
- Two remaining rotations: simultaneous readout chart on [q21,q27,q2 xor q14 xor q23,q12 xor q29,q4 xor q9], conditional on q3,q31. 35364 scored chart trials, 20 ordered readout pairs, multiple restarts. Data-map paid cost 40->23. Move each guarded quadratic phase to entry/shared-chart/exit and try 24 selector affine permutations; phase cost 17->11 (263->171 instructions). Final fragment 259 ops, 34 static paid, two unchanged parameterized rotations, physical 36 slots. SHA256 ce1ed88a22a1e84218c1a3e2e792493d946627a2196a0576c96376f4040cba59.
- Full reread/replay with presampled HMR record 462 and moved original rotation: exact BDD compositional comparison of individual rotation-control functions, Boolean phase, data, classical history, scope and final restoration on 3,133,452 legal inputs, 1,276 independent HMR variables. Candidate SHA256 72e3c0f04888832bc3c69bb6c59c633d2051b1c704905c33a7d6d381a8c195df; 51467 ops, 1523 CCX, 1641 static paid, 55 parameterized rotations, global37Q.
- Internal uniform-legal-input fair-HMR activation expected cost 1446.4375 -> 1484.9375 (+38.5). Not official cost. Source non-identically-zero function pressure cuts 3509 -> 3379. This is a function-support metric, not a physical-width proof. Source width and candidate width both 37.

## Exact chart witness

Branch h=s+2t, row masks in five coordinates (A,B,D,E,Z):
[16,10,1,2,4]; [2,8,4,1,16]; [3,16,2,10,4]; [7,2,11,8,16].
Read both complemented rotation predicates simultaneously at indices 0 and 2. Exit rows [13,10,4,8,16], [1,10,4,8,16], [7,10,4,8,16], [11,10,4,8,16]. The h=0 care set has Z=0. Rank-one transvections, dirty borrowed controls and affine basis changes are emitted and checked, not treated as free nonlinear operations.

## Research links and limitations

PR123-127 are independent donor work; do not sum their savings across parents. The n(log n)^(1/2+o(1)) Fourier manuscript (repair.tex, simultaneous spectral repair) motivates a shared predictor and exact sparse residual; dyadic flags and factored rare correction are a finite application, not a reproduction of its asymptotic batch construction. Its normalized inverse requires invertible group order. The 9/4 matrix exponent manuscript (shaving.tex) motivates multi-stage local tensor compression while accounting for lookup overhead; our GF(2) rank-one maps and guarded polynomial sharing are finite exact analogues, not an implementation of the asymptotic matrix algorithm. Local Lean identities are not the full oracle proof. P0-A/B/C/D and other issue #118 acceptance criteria remain open. No main merge or Kaggle mutation.

Reproduction bundle in research conversation includes pinned native source, BDD engine, search scripts, generated KMB fragments and hybrids, checks, and reproduction commands.
