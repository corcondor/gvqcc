# V8: cross-session union, global live permutation, nonlocal commuting hub
Research only; **NOT SUBMISSION**. Common original source SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03.
PR41's final PR40+41 union is pinned to 97623d3bb9b7fb61aeabd7312e869ab64e49da9c4070d359e79d86688c9161a5 (63113 ops, 1900 static, 1719.3125 expected, 55485/60766 source coverage). This is distinct from PR41's earlier 90.08% standalone.

| Step | Actual KMB SHA256 | Ops | Static paid | Expected paid | BDD checks |
|---|---|---:|---:|---:|---:|
| Exact transfer PR42+43 | 5a0563a6763421aee7b52c98657edb1bef9b86043688254823c63ba1c6350676 | 50165 | 1892 | 1716.3125 | 38823 |
| Dynamic zero/physical permutation | 43ae51a65ea4161c7ff1a6ab274ebc0bfd84b629a1943d1713e45aac69c241c8 | 42591 | 1887 | 1716.3125 | 50166 |
| Nonlocal versioned commuting hub | f7abc033dbed5477d5685225d9bf5fe262ceb888189ebcc3266ce23f9d15fd6d | 42599 | 1875 | 1704.3125 | 42376 |

Every stage independently re-read emitted KMB, compared all 3133452 legal inputs and 1174 independent potential HMR variables, state, original classical data, guard stack, relative phase and rotation controls; preserved 55 rotation instructions, 96 original certified 36Q bodies. 37Q complete diagnostic, still 5281 original source instructions outside complete certified chart coverage. No new complete gap, no new official score. 618 parent-serialized narrow operations in residual gap spans are not counted as newly covered source. Repeated execution not a new improvement.

## Algorithms
1. Match concrete PR42/43 old/new sequences on PR41 actual union, chart-aware interval scheduling, 1311 disjoint edits, no additive credit. 23 donors unmatched.
2. Exact zero-state/identity extraction; whole-trace DP on the logical occupant of slot 36 (1,856,105 state positions, 191 spans). Central frame is a physical/logical bijection; swap equal zero roles freely, nonzero exchanges require real SWAP. 2791 virtual unconditional SWAPs, 4846 exact identity deletions, 44 real exchanges, 37 zero-role switches, 19 final restores. Five deleted static paid gates have zero expected cost. Unlike previous logical affine/quadratic chart discovery, this is post-serialization physical allocation, preserves all previous chart bodies. No complete gap bridge; do not simply rerun identical zero-only DP.
3. Whole-trace same-SSA-guard commuting transvection families: maintain all currently transportable donor gates, allow HMR only when disjoint, respect conditional quantum dependencies and classical versions. Shared nonlinearity controls multiple targets using a CX-conjugated CCX, or cancels equal targets; 9482 pair-dependence checks, 12 candidate families, 11 selected disjoint spans, two spanning HMR and nine spanning classical guard scopes, 33->21 paid in selected slices. Full actual BDD verified (12 expected paid reduction). Do not repeat same fixed-control family scan. All emitted gates in these selected slices <=36Q. No claim of new general-purpose optimizer or cold-start 50% quota.
4. CommutingHubV8.lean contains 11 actual old/new gate lists with static guard masks from SSA flattening, phase, rotation observations, HMR record, and exact resources. Lean kernel CI must be checked before declaring proof success. This is not a whole quantum-channel or numerical oracle formal proof; BDD independently verifies reachability and all final observations.

## Conditional score model, not official
PR43 records C0=60927.54794503887, E0=1406.3125, Q0=37, S0=33.17031640530013. Hold other task costs and rotation overhead K=240.37798500105055 fixed. S(Q,E)=S0*(C0/(Q*(E+K)))^(1/3). V8 E=1704.3125 implies 31.38124 at 37Q, hypothetical 31.66916 at 36Q. At 36Q break-even E=1452.05390236114, needs >252.25859763886 additional expected paid reduction. 34 requires E<=1331.15424. No official verification or submission.

## Additional reading and source distinction
Prior refs PR29-43 (DeepMind, QAOA, Reqomp, XAG, phase basis, e-graphs) retained. New public references for this layout/dependency work, not external benchmark reproduction:
- DeCross et al., Qubit-Reuse Compilation with Mid-Circuit Measurement and Reset, https://doi.org/10.1103/PhysRevX.13.041057 (exact/greedy reuse compilation).
- Hua et al., CaQR, https://doi.org/10.1145/3582016.3582030 (dynamic reuse versus SWAP, gate count, duration).
- Paler, Wille, Devitt, Wire recycling for quantum circuit optimization, https://doi.org/10.1103/PhysRevA.94.042337 (lifetime-based wire allocation).
- Dynamic Quantum Circuit Compilation, https://doi.org/10.1109/TC.2025.3643826 (graph-based dynamic reuse).
- Tackling the Qubit Mapping Problem with Permutation-Aware Synthesis, https://ieeexplore.ieee.org/document/10313754/ (permutation-aware synthesis).
- Papakonstantinou, Systematic Synthesis and Optimization of Reversible Quantum Circuits via MINLP, Toffoli Permutation, and Local Search, https://doi.org/10.3390/quantum8030079 (comparison: bounded windows differ from our nonlocal HMR/SSA transport).
These are design inspirations, not claims of importing or reproducing their methods.

Reproduce from chat V8 archive and the pinned PR41/43/42 archives: run v8_integrate.py <root-containing-quotient-and-rankhub-extracts> in merged/union/central/global_chart, then v8_zero_scan.py, v8_layout.py, v8_commuting_hub.py. Prior source audit for ANGLE is incomplete, as recorded on #23: no ANGLE experiment started. Main unchanged.
