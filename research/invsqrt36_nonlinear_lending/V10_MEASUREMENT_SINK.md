# V10: measurement-sink transport and phase-only virtual register

Parent: PR #51 e314ab93bb92b68e5e82898fec7fe85eff030e3a9627fe1fcba470ffbf78b30c native SHA; separate width parent 5a35e7a5126dcbf979288c0cc8ad4f1c38af8729cbd591d0ccfc917a831fc9a0. Read PR52 full-domain verification before considering PR50 donors; PR51 already incorporated those donor edits. No double counting.

## New results (research diagnostic only)

- Basic HMR transport: 6 options, 3 selected spans, 4 CCX removed, all 3,133,452 legal inputs and 1,174 independent event variables; 42,053 paired checks PASS. 1,693.3125 -> 1,689.3125 expected paid. Not added to deep route.
- Nested-guard transport: 4,909 backward instruction visits, 8 alternatives, 5 selected spans [174,227), [6142,6159), [6177,6200), [20449,20460), [22476,22553). 6 CCX -> classically conditioned CZ. Full exact replay PASS (41,968 comparisons). Native SHA 3e018248aefbc5dc70f411ee72da9bb8ecc9c147e53ab2e5be8e50eb43d14322. 42,144 ops, 1,857 static / 1,687.3125 expected paid.
- New phase-only virtual register: source [26344,26426), corresponding native [16850,16932), q36 exactly zero on entry, q36=q27*q28 XOR q27 XOR q25, phase read q36*(1 XOR q2 XOR q18). Direct phase synthesis on 36 wires; normalize HMR 16886 only after exact whole-span proof for arbitrary original measurement result, subsequent HMR overwrites classical register 483. Source/candidate state, sign, rotations, classical state and active guards equal. Exact full paired replay PASS (42,063 checks), 1,174 original independent event variables, candidate 1,173. Cost unchanged. Coverage 55,485 -> 55,567/60,766 (91.44423%). This source interval is already covered by a different PR44 macro; our novelty is the cost-first path and phase-only architecture, not an unprecedented source interval.
- Final sign-phase cleanup removes seven free phase gates by independent exact coefficient ledger; no further paid reduction. Native final SHA256 9856cf6c5d58c0e2e42c74be2312ea17e810114685beab22899ad850cb99e2b4. 42,138 ops, 1,857 static / 1,687.3125 expected, 1,173 HMR, 55,567 coverage, dependency depth 24,321 vs 24,341. Both 37Q.
- Separate width-first nested transport: 4 CCX removed, 43,161 instructions, 1,895 static / 1,714.3125 expected, 55,829/60,766 (91.87539%). 42,968 exact checks PASS. SHA256 99b81acc2ef947dc753abe3e3257df3ca6ab71b1042f4febede435944085f20f. No cross-parent addition.
- Score model: Q37 E1687.3125 -> 31.4732195744; hypothetical Q36 -> 31.7619808379; still >235.25859764 expected paid reduction needed at Q36 to beat 33.1703164053. Overhead and other tasks fixed. No complete36Q, official verifier or score improvement; do not merge/submit.

Lean: five concrete Boolean spans, universal sink identity and parity fold, virtual accumulator phase identity. Full-domain reachable-state premises and removed-event independence are established separately by BDD. Check CI before claiming Lean PASS.

## Literature / code
- Yang and Yuan, MBUndo: Sound, Automatic, and Efficient Measurement-Based Uncomputation, https://arxiv.org/abs/2611.02345 (previously cited, now directly applied).
- Gidney, Halving the cost of quantum addition, https://arxiv.org/abs/1709.06648 (previous reference).
- Quantum circuit optimization with AlphaTensor, https://doi.org/10.1038/s42256-025-01001-1 ; public source https://github.com/google-deepmind/alphatensor_quantum (phase gadget sharing).
- Sharma and Achour, Optimizing Ancilla-Based Quantum Circuits with SPARE, https://doi.org/10.1145/3729253 (compute/uncompute restructuring; video https://www.youtube.com/watch?v=or7qQXxQ2uE).
- Gu et al., Discovering state-of-the-art quantum circuits with large language models, https://arxiv.org/abs/2610.22367 ; https://github.com/andigu/uncompute (previously surveyed; arithmetic design and verification comparator).
- Modular Synthesis of Efficient Quantum Uncomputation, https://doi.org/10.1145/3689785 (previous reference).
- DeepMind https://github.com/google-deepmind/formal-quantum-computation (prior proof-oriented inspiration).
- Ichikawa et al. https://arxiv.org/abs/2503.09356 (prior combinatorial search inspiration; QAOA not run in V10).

All new code independently written, no external source copied. Reproduce in companion archive: cd merged/union/central/global_chart; python v10_sink_deep.py; python v10_sink_deep.py --wide; python v10_phase_only_virtual.py; python v10_phase_clean.py. Earlier simple screen: python v10_sink.py. Preserve parent files. Main unchanged.
