# V56: reciprocal conditional basis and measured prefix scheduling

RESEARCH ONLY — NOT SUBMISSION. Parent #131, identical exact adaptive coset phase plan. No new approximation. No 37Q circuit emitted or needed for reproduction. Parent 35Q: 3,371 CCX / 8,549 rotations / 87,821 ops / 2,849 HMR.

| Q | CCX | Generic rotations | Ops | HMR | SHA256 |
|---:|---:|---:|---:|---:|---|
|32|2614|8541|78218|2142|f12c63a72d100097297e3e96e5b56bf36eb14e36313e169d3521fa880500699b|
|34|2018|8541|76100|2018|578130414bc4e773ce3a8e6351b8119deead639399e75830821520ed2b1d6bba|
|35|1912|8541|75660|1912|87de4a23d41a1f1b755ecc669b455fe62d537cc5fe3b621969b959d3f1f10452|
|36|1805|8541|75244|1805|20c1652b95706b7fe13dc3b23a1822751daf6c5829afee0f0ffdc4ddfd030097|

All four independently serialized and checked using unchanged #131 verifier: full 4,194,304 rotation-control rows, independent HMR sign correction, restored data and scratch, exact modular 128-bit phase contraction, and squared tolerance on all 3,133,452 legal inputs PASS. Worst ratio 0.8489570934325457. No official verifier or competitive score; thousands of generic rotations remain.

## Three stages
- Exact integer sign/representative audit: 7427 cosets, 4148 movable after fixing zero-containing cosets to their direct representative. All coefficients positive and character signs homogeneous; no nonempty exact cancellation. 634 forced nonzero frequencies. HiGHS MILP optimum reported 481 additional support, zero gap; 1123→1115 compensation rotations. Restricted to fixed decomposition and direct-zero convention. Solver optimum not Lean-certified.
- Conditional basis: compute f * <v_j,x> once for each cached basis vector, obtain all conditional affine first predicates by XOR; retain selected basis vectors across batches; HMR clear stale vectors using parent flag and input parity. Exact reconstructibility checked during emission. At 36Q, 2155 of 2174 first predicates served with 969 basis products, plus 19 direct products: 2174→988. 630 second-condition products retained. Their summed fixed quadratic rank is 626 (restricted audit, not a universal gate lower bound). Intermediate 34Q/35Q/36Q circuits 2476/2309/2139 CCX independently verified.
- Joint prefix-cut/basis capacity DP and clean measured prefix ladder. When sufficient clean work lines exist, a d-bit direct prefix compute+erase costs 2d-3 paid gates (d>=2); otherwise prior dirty-MCX fallback. DP optimizes selected candidate batch costs and prefix cuts, not a globally optimal circuit.

## Reproduction
Full actual native emitters, 32/34/35/36Q circuits, exact input plan, fixed representative assignment, tags, Python and C++ independent verifier, logs, Lean source and SHA256 manifest: GVQCC_V56_ReciprocalBasis_NOT_SUBMISSION.zip supplied in conversation; archive SHA256 f3c95d6ebd51bb11ae7f14a5ff2027f512cef4eb9b3fe71736089674bfa313e4. 25Q format template. In-repo compact quotient planner and local Lean identities; not full KMB semantics formalized. CI must pass before claiming Lean compilation.

References: OpenAI finite Fourier transforms, 2026-11-24 (common eigenbasis, prediction and repair) https://github.com/openai/math/tree/main/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026 ; matrix multiplication exponent nine fourths (local concentration, trivalent compression) https://github.com/openai/math/tree/main/preprints/The-matrix-multiplication-exponent-is-nine-fourths-November-24-2026 . Finite GF(2) reciprocal-basis analogy only; no transfer of asymptotic exponents to CCX complexity. No main/Kaggle mutation.
