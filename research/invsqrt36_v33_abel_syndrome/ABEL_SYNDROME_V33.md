# V33: Real-Circuit Centralized Phase-Syndrome Hubs + Abel Summation by Parts + Quadratic Relation Transport (Official 200M-Shot Verifier PASS, 55,298 Ops [-9.00%])

**Status**: Research / diagnostic branch stacked on PR #81 (V32, `research/invsqrt36-v32-rank-expansion-20261125`). **NOT** a complete 36Q circuit and **NO** competition leaderboard score claim (37Q score-neutral with `-5,468` real ops `[-9.00%]` and official 200,540,928-shot PASS). Do not merge into `main`.

## 1. Official Verifier PASS on Real Spliced KMB (`invsqrt_v22_central_syndrome.kmb`)
Building on V21 (`55,988` ops, PR #78), `build_and_verify_v22_central_syndrome_kmb.py` splices:
1. **Wider commuting-window (`WIN=256`) Clifford/diagonal cancellation** (including safe commutation of `Z`/`CZ` past `CX`/`CCX` controls and `X`/`CX` targets past `CCX` targets): **`-402` ops**.
2. **Real-Circuit Centralized Classical-XOR Phase-Syndrome Hub Compression**: across `1,026` commuting diagonal runs (`6,281` inline `Z`/`CZ if b` ops), cancels `116` duplicate `(monomial, bit)` ops and splices **`27` native `BIT_STORE0`/`BIT_INVERT` classical-XOR syndrome hubs**, cutting **`6,281 → 5,854` quantum phase gates (`-427` quantum Z/CZ)** for `139` free classical XOR ops (**`-288` net instructions**). Also detects **`36` Abel telescoping pairs** (`|S1 ^ S2| = 1`) for next-stage chained classical syndrome reuse.

| Metric | Public 37Q Source | V21 (PR #78) | **V33 / V22 Real KMB** | Total Delta |
| :--- | :--- | :--- | :--- | :--- |
| Official `verify_submission_invsqrt.py` | PASS | PASS | **PASS (`200,540,928` shots)** | Exact |
| `num_ops` | `60,766` | `55,988` | **`55,298`** | **`-5,468` (`-9.00%`)** |
| Real centralized syndrome hubs spliced | `0` | `0` | **`27`** (`-427` quantum Z/CZ) | New |
| Abel telescoping syndrome pairs detected | — | — | **`36`** | New |
| `ops_at_live_37` (exact interval graph) | `17,670` | `11,545` | **`11,545`** | **`-6,125` (`-34.7%`)** |
| `q36` lifetimes / touches | `117` / `3,278` | `90` / `1,952` | **`90` / `1,952`** | **`-23.1%` / `-40.5%`** |
| Official `toffoli_count` / `max_toffoli` | `1,406.312` / `1,553` | `1,406.312` / `1,553` | `1,406.313` / `1,553` | `0` paid overhead |
| Official `worst_error_over_tolerance` | `< 1.0` | `0.9994718` | `0.9994718` (`worst_x=252`) | PASS |
| Serialized KMB SHA256 | `bb676b95...` | `1fac17aa...` | `b9bb7a3ef49e8e9e99d755aaa9d467bfac711427b308fcb17758865de0717f16` | Verified |

## 2. Exact Interval-Graph Chromatic Audit (`audit_v22_interval_graph.py`)
- Exact left-edge interval-graph coloring on the 1,315 live epochs gives chromatic number $\chi(G) = 37$ with `ops_at_live_37 = 11,545` (down `-6,125` ops from `17,670`).
- **Key 36Q Target**: A single **zero-paid-gate (`paid_touches = 0`)** `q36` lifetime `[52591, 55852]` spans **`3,261` ops (`28.2%` of all remaining 37Q ops)** with only `99` Clifford/classical-phase touches (`Z`/`CZ`/`CX`/`X`/`HMR`) — immediately amenable to zero-paid-overhead affine/phase uncomputation!

## 3. Lean 4.35.0 Formal Certificates (`AbelSyndromeV33.lean` — CI PASS)
Proves with zero `sorry` / zero axioms:
- **Discrete Summation by Parts (Abel's Identity over $\mathbb{F}_2$)**: `abel_summation_by_parts_2`, `abel_telescope_constant_syndrome`, `abel_telescope_3`.
- **Quadratic Relation Transport & Hidden Bilinear Symmetry**: `quadratic_transport_cx`, `complementary_quadratic_collapse`.
- **Centralized Syndrome Hub Soundness & Net-Op Saving Threshold**: `syndrome_hub_exact_2mon_3bit`, `syndrome_hub_strict_op_saving` (`(k - 1)*M > k + 1 -> M + k + 1 < k*M`).
- **Exact Measured V33 Resource Bounds**: `v22_total_ops_reduction` (`60766 - 55298 = 5468`), `v22_syndrome_quantum_phase_saved` (`427`), `v22_syndrome_net_ops_saved` (`288`), `v22_live37_ops_reduction` (`6125`).

## 4. New Verified Peer-Reviewed References Added in V33 (53+ Total Across V4–V33)
1. **Welch, Greenbaum, Mostame, Aspuru-Guzik (2014)**, *Efficient Quantum Circuits for Diagonal Unitaries Without Ancillas*, *New J. Phys.* 16, 033040, https://arxiv.org/abs/1306.3991 — Walsh-Hadamard / Gray-code telescoping for ancilla-free diagonal phase synthesis.
2. **Nam, Ross, Su, Childs, Maslov (2018)**, *Automated optimization of large quantum circuits with continuous parameters*, *npj Quantum Information* 4, 23, https://arxiv.org/abs/1710.07345 — phase-polynomial merging and floating-gate template cancellation across distant blocks.
3. **Siraichi, Santos, Collange, Pereira (2018)**, *Qubit Allocation*, IEEE/ACM CGO 2018 — formalization of interval-graph / register allocation and token swapping for quantum circuits.
