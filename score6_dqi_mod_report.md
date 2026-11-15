# Bounded DQI algebraic self-target MBU search

## Result

No new circuit was produced. Four discovery models found no eligible CCX whose post-gate target is the constant zero or one. The accepted e4 circuit was left byte-for-byte unchanged. This result is limited to the models below; it is not an impossibility result for measurement-based uncomputation or for DQI optimization.

Input: `/workspace/scratch/3815fb5fae06/score5_norm_final/dqi.kmb`, SHA256 `e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`. It contains 58,868,734 instructions, 363,654 CCX, and 12,240 CSWAP. The accepted resource figures remain Q=889, static Toffoli=382,894, and local official mean Toffoli=382,066.52936523437. This work adds no native or official whole-circuit verification and makes no Public Score claim.

## Why this was a distinct opportunity

The prior `score5_dqi_xag_scan.cpp` and `score5_dqi_xag_span.cpp` deliberately excluded the current CCX target from the candidate cache. They therefore did not test whether the gate itself clears a cached product.

On the proved input subspace t=ab, the operation CCX(a,b,t) can be replaced by measuring t in the X basis and resetting it (HMR), then applying CZ(a,b) conditioned on the fresh measurement result. For outcome m, HMR contributes phase (-1)^(mab), and the conditional CZ cancels it. The target exits zero. This equality is an instrument identity on the complete reachable subspace, including entangled references; discovering t=ab on sampled inputs alone is insufficient. For t=1+ab, X before and after that replacement gives the required constant-one output with the same exact phase cancellation.

The relevant primary precedent is Craig Gidney, *Halving the cost of quantum addition*, Quantum 2, 74 (2018), https://arxiv.org/abs/1709.06648 and https://doi.org/10.22331/q-2018-06-18-74. Its temporary logical AND construction motivates the measurement-erasure step. No claimed saving was imported from the paper without a matching circuit site.

## Implemented discovery models

| Model | CCX sites analyzed | Reused product signatures | Eligible candidates |
|---|---:|---:|---:|
| Exact-form XOR/AND signatures, conservative guard barriers | 318,745 | 4,350 | 0 |
| 1,024 Boolean valuations with actual AND | 318,745 | n/a | 0 |
| Executed branch arm, snapshot and conservative join | 363,654 | 4,404 | 0 |
| Executed arm plus exact Fredkin algebra | 363,654 | 6,703 | 0 |

Each initial quantum wire is an independent symbolic variable. Unconditional R/HMR creates a known zero. Explicit conditionally written quantum values are conservatively forgotten. In the branch models, PUSH saves the incoming symbolic state; the executed arm is analyzed normally, and POP retains only values equal to their saved incoming expressions. Changed values are replaced by independent fresh symbols. Thus branch-local compute/uncompute is visible without assuming the branch ran globally.

The Fredkin model uses d=a*(b+c), then b+=d and c+=d, in the Boolean ring. This preserves correlations that the old scanners lost by forgetting both swapped wires.

The exact-form models use 128-bit expression fingerprints and structural product interning. They do not expand arbitrary polynomial identities, so even a discovered match would need a separate exact symbolic certificate. The 1,024-valuation model uses deterministic pseudorandom discovery inputs, not the competition seeds or salts. Its initial 2,904 apparent zeros all had an entirely zero product panel: they occurred in long rare-event AND predicates. Those panels were expressly rejected as evidence, leaving zero eligible candidates. This filter may also reject true but unobserved rare identities; it is not a proof of their absence.

## Checks and reproduction

`score6_dqi_mod_zero_checks.py` creates six tiny KMB fixtures: direct product clearing, constant-one clearing, a dirty accumulator, a conditional arm, a pair of Fredkin gates, and a changed control. All 24 model/fixture checks pass, including positive matches and the expected negative barriers. These are discovery-scanner checks, not a production circuit qualification.

Build each C++17 scanner and run it on the pinned e4 input:

```bash
g++ -O3 -std=c++17 score6_dqi_mod_zero_scan.cpp -o /tmp/score6_dqi_mod_zero_scan
/tmp/score6_dqi_mod_zero_scan /path/to/e4/dqi.kmb score6_dqi_mod_zero_scan.json
```

Repeat with the suffixes `truth`, `branch`, and `cswap`. Place the four executables in a single directory, then run:

```bash
python score6_dqi_mod_zero_checks.py --binary-dir /path/to/binaries --out score6_dqi_mod_zero_checks.json
```

The manifest binds each authored source and saved discovery result. Runtime was approximately 0.59, 1.11, 1.63, and 3.19 seconds respectively in this environment. No new large synthesis search was started under this MBU scope.
