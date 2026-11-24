# V8 mixed-guard transport + nested clean quintic hubs (NOT SUBMISSION)

Base is PR #41 (91.3092847974% coverage); reviewed PRs #39–43. Imported PR #43 using exact native subsequence matching, chart-boundary checks and disjoint weighted interval scheduling. 1333 matching donor candidates, 1326 selected. PR #42 replacement was considered but not selected; do not add its claimed savings.

## Reproduced results
| Diagnostic | instructions | static paid | expected paid | covered source ops | exact BDD comparisons |
|---|---:|---:|---:|---:|---:|
| PR41 integrated |63113|1900|1719.3125|55485|62566|
| donor |50070|1894|1718.3125|55485|38727|
| mixed |47216|1894|1718.3125|55485|35571|
| wide |47094|1914|1727.3125|55829|46869|

All 3,133,452 legal inputs and arbitrary measurement histories under the existing exact symbolic model. Wide checks 1,186 independent HMR variables. Wide coverage 91.87539084356%, 4,937 source ops remain outside verified 36Q charts. Native circuit overall still 37Q. Neither candidate is an official submission or score improvement. See JSON receipt for SHA256.

## New experiments
1. Transport phase polynomials forward/backward across unconditional nonlinear CCX/CSWAP data scaffolds, preserving the reversible data map, classical writes, rotations and measurements. Group monomials by equal guard signatures (transpose the guard/monomial incidence matrix) and form classical XOR controls. Search complete epochs and lengths 4,8,16,32,64, 6,293 windows / 24,872 trials / 1,789 positive candidates / 551 disjoint accepted, 208 containing nonlinear data scaffolds and 54 transposed. Added 140 classical bits. Local [41029,41037) 8→5 native gates, same CCX count.
2. Residual affine chart endpoint with rank deficiency >=3 leaves two clean physical carriers after projecting a 37th wire. Degree-five phase synthesis using nested ANDs, HMR uncompute and conditional CZ corrections, while preserving original measurement histories. Five layers of GF(2) shear search, beam width 12: 17,738 coordinate trials, 976 emitted candidate trials; all four selected native bodies pass exact local verification. Ranges [24732,24816), [26344,26426), [27381,27471), [27897,27985), +344 source coverage, +20 static and +9 expected paid. Re-integrated into mixed candidate with full replay. Separate cost-first and width-first candidates: do not silently adopt wide if cost dominates.

## Formalization and reproducibility
MixedQuinticV8.lean proves three concrete Boolean phase identities, local resource counts, nested measured-hub phase identity and shared guard law. It does not prove the entire KMB, reachable-state rank assumptions, or official scoring. CI pinned Lean 4.35.0.
Reproduction archive distributed to user: GVQCC_V8_MixedQuintic_91p88_NOT_SUBMISSION.zip; from union/central/global_chart run v8_donor.py, v8_cross_guard.py, v8_degree5.py, v8_union.py. Exact gate lists/measurements and chart ranges in generated JSON receipts. Separate two peer inputs included. No competition upload. 

## Conditional score projection
Reuse PR43 model only: S=S0*(C0/[Q(E+K)])^(1/3), S0=33.1703164053, C0=60927.54794503887, K=240.37798500105055. 36Q break-even expected paid 1452.05390236114. At 37Q mixed projects 31.30629 and wide 31.25849. At hypothetical fully 36Q with no further paid increase: 31.59352 / 31.54528. Wide needs >275.2586 additional expected-paid savings; this is a budget not a lower bound. Need full valid native 36Q KMB and real verifier; lowering free instructions is not alone a score gain.

## Additional literature investigated (deduplicate against previous PR bibliographies)
- Boyar, Peralta, A New Combinational Logic Minimization Technique with Applications to Cryptology (2010), https://doi.org/10.1007/978-3-642-13193-6_16 — separate nonlinear and linear costs.
- Boyar, Matthews, Peralta, Logic Minimization Techniques with Applications to Cryptology (2013), https://doi.org/10.1007/s00145-012-9124-7 — shared XOR straight-line programs.
- Boyar, Find, Peralta, Small Low-Depth Circuits for Cryptographic Applications (2018 online/2019 issue), https://doi.org/10.1007/s12095-018-0296-3 — depth-constrained linear optimizer.
- Cowtan et al., Phase Gadget Synthesis for Shallow Circuits (2019), https://arxiv.org/abs/1906.01734 — phase grouping and synthesis.
- Meuli et al., The Role of Multiplicative Complexity in Compiling Low T-count Oracle Circuits (2019), https://arxiv.org/abs/1908.01609 — AND count and ancilla tradeoff; SAT-based pebbling.
- Bu, Reversible Circuit Synthesis Method by Combining Factoring and Boolean Expression Diagram (2021), https://doi.org/10.3724/SP.J.1089.2021.18738 — shared ESOP factorization.
- Clarino et al., Leveraging Different Boolean Function Decompositions to Reduce T-Count in LUT-Based Quantum Circuit Synthesis (2025), https://doi.org/10.1587/transinf.2024EDP7194 — alternative Shannon/Davio/relative-phase synthesis.
- Nemirovsky et al., Phase gadget compilation of quantum circuits using multiqubit gates (2025), https://arxiv.org/abs/2510.16788 — phase grouping; hardware primitives not directly portable to KickMix.

References motivate design choices only; their implementations and claimed savings are not asserted to have been reproduced.
