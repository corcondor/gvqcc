# V7 Centralized Phase-Basis Compression & Deep 37Q Hotspot Audit

**Status**: Research / diagnostic branch stacked on PR #37 (`research/invsqrt36-joint-delta-v6-20261124`). **NOT** a complete 36Q submission, **NOT** an official verifier pass, and **NO** competition score claim. Do not merge into `main`.

## 1. Cross-Session Alignment (PR #29 – PR #38)
- **PR #36 (V6 Phase Hub)**: 53,749 / 60,766 ops (**88.45%**) in 36Q charts, 7,017 remaining, 1,904 static / 1,721.8125 expected paid. Identified the V7 centralization target:
  $$\phi(x, m) = \bigoplus_{i=1}^{r} h_i(m)\,P_i(x)$$
- **PR #37 (V6 Joint Delta)**: Removed 11 paid gates directly on top of PR #36 -> **1,893 static / 1,710.8125 expected paid** at 88.45% coverage.
- **PR #34 (V6 Multi-Pattern)**: Formalized Takahashi 0-ancilla, Hybrid Gidney–Cuccaro/Takahashi peak-shaving (`n + k` CCX vs V4 `n + 2k`), amortized shared-context bridge (`m + 2` vs `3m`), and conditionally-clean borrow + Maslov relative-phase cancel.

## 2. V7 Deep Search Results on Real 60,766-Op 37Q `invsqrt.kmb`

### A. Stack-Exact `PUSH_CONDITION` Centralized Phase-Basis Compression (`scan_v7_push_condition_phase_basis.py`)
Tracking all `2,271` `PUSH_CONDITION` / `2,271` `POP_CONDITION` frames (`5,166` Z, `11,879` CZ, `41` CCZ, `17` Z_POW) with exact per-qubit computational-basis `write_epoch` coordinates proves substantial GF(2) centralization structure directly in the real circuit:

| Metric | Value |
| :--- | :--- |
| `PUSH_CONDITION` / `POP_CONDITION` pairs | 2,271 / 2,271 |
| Distinct active classical conditions | 1,439 |
| Non-zero deg-1+ conditioned phase polynomials | 1,439 → **GF(2) rank 1,410** (**29 redundant**) |
| Non-zero deg-2+ conditioned phase polynomials | 935 → **GF(2) rank 892** (**43 redundant**) |
| Unique epoch-exact deg-2 monomials | 9,830 |
| Shared deg-2 monomials across distinct conditions | **910** |
| Max single-monomial reuse count | **21×** on `(q4, ep=232) * (q21, ep=490)` |
| Top 5 reused monomials (all share hub `(q21, ep=490)`) | `(4,232)*(21,490)` ×21, `(2,347)*(21,490)` ×17, `(14,204)*(21,490)` ×16, `(6,264)*(21,490)` ×16, `(5,248)*(21,490)` ×14 |

### B. Deep Dissection of 37Q Peak-Width Hotspots (`deep_search_v7_central_phase_and_blocks.py`)
- **8 period-112 7-bit arithmetic rows** (`[8099, 8150]` .. `[8963, 9014]`): each is 52 ops, `7` CCX, `6` HMR, **`touchedQ = 20`** → **`17` completely idle dirty qubits** available for dirty-ancilla / peak-shaving!
- **3 large 19–21-bit ripple chains** (`[7706, 8032]`, `[9526, 9788]`, `[9850, 10185]`): `23–29` CCX, `19–24` HMR, **`touchedQ = 21–23`** → **`14–16` idle dirty qubits**!
- **Tail uncomputation plateau** (`[57893, 60664]`): `2,772` ops at `live = 37Q`, yet **only `2` CCX and `1` HMR** (99.9% Clifford / classical phase cleanup!).

## 3. Lean 4.35.0 Formal Certificates (`CentralPhaseHubV7.lean`)
Proved with zero `sorry` / zero axioms under Lean 4.35.0 CI:
- `central_phase_basis_compress_3to2`, `central_phase_basis_compress_4to3`, `central_phase_linear_step_2`: exact bilinear GF(2) phase-basis compression `phi(x, m) = XOR_i h_i(m) B_i(x)`.
- `shared_wire_hub_factor3`: shared hub-wire monomial factorization (modeling the 21× `(q21, ep=490)` hub).
- `v7_deg2plus_compression_count` (`935 - 892 = 43`), `v7_deg1plus_compression_count` (`1439 - 1410 = 29`), `central_basis_strict_saving`.
- `hotspot_idle_dirty_qubits` (`touched <= 23 -> 37 - touched >= 14`) and `phase_clifford_cancel`.

## 4. Extended Verified Literature Survey (9 New Papers Added in V7 -> 42+ Total Across V4–V7)

### New Verified References Added in V7
1. **Amy & Mosca (2019)**, *T-count optimization and Reed-Muller codes*, *IEEE Trans. Inf. Theory* 65(8):4771–4784, https://arxiv.org/abs/1601.07363 — equivalence between phase-polynomial compression and Reed-Muller decoding.
2. **Low, Kliuchnikov, Schaeffer (2024)**, *Trading T gates for dirty qubits in state preparation and unitary synthesis*, *Quantum* 8, 1375, https://arxiv.org/abs/1812.00954 — directly exploits the 14–17 idle dirty qubits inside 37Q arithmetic hotspots.
3. **de Beaudrap, Bian, Wang (2020)**, *Fast and effective techniques for T-count reduction via spider nest identities*, TQC 2020, https://arxiv.org/abs/2004.05164 — spider-nest phase-gadget cancellation across distant blocks.
4. **Chareton, Bardin, Bobot, Perrelle, Valiron (2021)**, *An Automated Deductive Verification Framework for Circuit-building Quantum Programs* (Qbricks), ESOP 2021, https://arxiv.org/abs/2003.05841 — parametric path-sum deductive verification for quantum arithmetic.
5. **Gidney (2019)**, *Asymptotically Efficient Quantum Karatsuba Multiplication*, https://arxiv.org/abs/1904.07356 — linear-space (`O(n)`) in-place recursive multiplication via tail-call output accumulation.
6. **Campbell & Howard (2017)**, *A unified framework for magic state distillation and multi-qubit gate-synthesis with reduced resource cost*, *Phys. Rev. A* 95, 022316, https://arxiv.org/abs/1606.01904 — symmetric 3-tensor / phase-polynomial rank compression.
7. **Litinski (2019)**, *A Game of Surface Codes: Large-Scale Quantum Computing with Lattice Surgery*, *Quantum* 3, 128, https://arxiv.org/abs/1808.02892 — Pauli-based measurement-driven Clifford+T space-time tradeoffs.
8. **Komarath, Sarma, Sawlani (2016)**, *Pebbling Meets Coloring: Reversible Pebble Game On Trees*, https://arxiv.org/abs/1604.05510 — polynomial-time reversible pebbling bounds on trees.
9. **Bhattacharjee, Soeken, Dutta, Chattopadhyay, De Micheli (2019)**, *Reversible Pebble Games for Reducing Qubits in Hierarchical Quantum Circuit Synthesis*, ISMVL 2019 — hierarchical width reduction via reversible pebbling.

*(Retains all 33+ verified papers from PR #29, #31, #32, #34, #36, #37 including Takahashi 2010, Khattar–Gidney 2025, Häner–Roetteler–Svore 2018, Meuli 2019, Maslov 2016, Gidney 2019 Windowed, Kissinger–van de Wetering 2020, Heyfron–Campbell 2018 TODD, Amy–Maslov–Mosca 2014, Vandaele 2022, Seidel 2024 Qrisp, VOQC 2021, PhasePoly 2025, QCLA 2006, etc.)*
