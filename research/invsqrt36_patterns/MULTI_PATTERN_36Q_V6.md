# Multi-Pattern 36Q InvSqrt Strategy (V6): Peak-Shaving Arithmetic, Amortized Context Bridges, and Extended Literature Survey

**Status**: Research / diagnostic branch stacked on PR #32 (`research/invsqrt36-shared-lifetime-v5-20261124`). **NOT** a complete 36Q submission, **NOT** an official verifier pass, and **NO** competition score claim. Do not merge into `main`.

## 1. Cross-Session Synthesis (PR #27 – PR #32)
Across PR #27 (V3), PR #28 (Lean certificates), PR #29 (V4 conditional carry bridge), PR #30 (phase-derived open hub), PR #31 (V5 adaptive nonlinear atlas), and PR #32 (V5 shared-lifetime + virtual HMR), the 37Q `invsqrt.kmb` (60,766 source ops, 1,553 static Toffoli-like, 1,406.3125 expected paid) has reached:
- **PR #32 (V5 shared-lifetime)**: 51,725 / 60,766 ops in 36Q charts (**85.12%**), 1,755 static / 1,608.3125 expected paid (**9,041 ops remain**).
- **PR #31 (V5 adaptive atlas)**: 53,195 / 60,766 ops in 36Q charts (**87.54%**), 1,879 static / 1,705.3125 expected paid (**7,571 ops remain**).

### Real 60,766-Op `invsqrt.kmb` Peak-Width Structural Audit
Running `analyze_invsqrt_36q_patterns.py` on the 37Q `invsqrt.kmb` (`num_instructions=60,766`, `num_toffoli_like=1,553`, `num_t_like=10`, `total_ccx=1,470`, `total_hmr=1,278`) reveals why single-stage chart replacement hits a wall:
- **Exact 37Q liveness**: `17,670` ops (`29.08%`) sit at `live = 37Q`, partitioned into `387` contiguous spans containing **`477` CCXs** and **`400` HMRs** across **`157` CCX blocks**.
- **Top 37Q arithmetic clusters**:
  - Large ripple chains: `[9526, 9788]` (`21` CCX), `[9850, 10185]` (`21` CCX), `[7706, 8032]` (`19` CCX), `[13606, 13723]` (`16` CCX), `[37923, 38177]` (`10` CCX) — directly matching the V4 bridge sites (`7754, 7912, 8096, 9735, 10041, 10114, 10175`).
  - Repeated period-112 7-bit arithmetic rows: `[8099, 8150]`, `[8291, 8342]`, `[8403, 8454]`, `[8515, 8566]`, `[8627, 8678]`, `[8739, 8790]`, `[8851, 8902]`, `[8963, 9014]` (`7` CCX each, exact `+112`-op stride).
  - Longest 37Q live-wire plateaus: `[57893, 60664]` (`2,771` ops), `[30051, 31170]` (`1,119` ops), `[33035, 33960]` (`925` ops), `[19465, 20387]` (`922` ops).

## 2. Four Complementary 36Q Patterns (Exhaustively Verified + Lean 4.35.0 Certified)

| Pattern | Mechanism | Paid CCX Cost | Extra Ancillae | Targets | Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1: Takahashi 0-Ancilla Adder** | In-place operand carry-propagation (`arXiv:0910.2530`) | `2n - 2` (`mod 2^n`) | **0** | Unresolved 37Q carry gaps (100% coverage, no context `h` needed) | Python exhaustive (`n=3..6`, up to 4,096 cases) + Lean `takahashi3_correct` |
| **A2: Hybrid Gidney–Cuccaro/Takahashi Peak-Shaving** | Gidney (`1 CCX/bit`) on low `n - k` bits + Cuccaro/Takahashi (`2 CCX/bit`) ONLY on `k` 37Q-peak bits | **`n + k`** (vs V4 `n + 2k`, V3 `n + 4k`) | **`-k` qubits** | Period-112 7-bit rows & 19–21-bit ripple chains (`+1 CCX` per saved qubit!) | Python exhaustive (`n=4,6`, `k=1,2`) + Lean `hybrid4_correct`, `hybrid_beats_v4_on_peaks` |
| **B: Amortized Shared-Context Bridge** | Materialize shared quadratic factor `q` once across `m` carry stages (`h_i = q ⊕ l_i`) | **`m + 2`** (vs V4 `3m`) | **0** (dirty carrier) | Directly solves PR #29's open amortization bottleneck (`-2(m-1)` CCX) | Lean `amortized2Stage_correct`, `amortized_beats_v4` |
| **C: Conditionally-Clean Borrow & Relative-Phase Cancel** | Borrow `d` where `g=1 => d=0` (`arXiv:2407.17966`) + Maslov compute/uncompute phase cancellation (`arXiv:1508.03273`) | No toggle-detection `2x` penalty | **0** | High-width uncomputation plateaus (`[57893, 60664]`, etc.) | Lean `condCleanBorrow_correct`, `relative_phase_cancel` |

## 3. Extended Peer-Reviewed Literature Survey (10+ New Papers Beyond V4/V5's 18 = 28+ Total)

### New References Added in V6 (Verified arXiv / DOI)
1. **Takahashi, Tani, Kunihiro (2010)**, *Quantum Addition Circuits and Unbounded Fan-Out*, QIC 10(9–10):872–890, https://arxiv.org/abs/0910.2530 — 0-ancilla in-place ripple-carry addition (`2n - 2` CCX mod `2^n`), directly enabling Pattern A1/A2 on unresolved 37Q carry stages without context search.
2. **Khattar & Gidney (2025)**, *Rise of conditionally clean ancillae for efficient quantum circuit constructions*, *Quantum* 9, 1752 (2025), https://arxiv.org/abs/2407.17966 — conditionally clean ancillae & laddered toggle detection, bridging clean and dirty qubit borrowing in the EFTQC low-qubit regime (Pattern C).
3. **Häner, Roetteler, Svore (2018)**, *Optimizing Quantum Circuits for Arithmetic*, https://arxiv.org/abs/1805.12445 — piecewise polynomial & Newton–Raphson inverse square root (`1/sqrt(x)`) register-reuse circuits, directly targeting GVQCC's `invsqrt` oracle structure.
4. **Meuli, Soeken, Roetteler, Bjorner, De Micheli (2019)**, *Reversible Pebbling Game for Quantum Memory Management*, DATE 2019, https://arxiv.org/abs/1904.02121 — SAT-based exact width-constrained pebbling on data-dependency DAGs for 36Q memory scheduling.
5. **Maslov (2016)**, *On the advantages of using relative-phase Toffolis with an application to multiple control Toffoli optimization*, *Phys. Rev. A* 93, 022311, https://arxiv.org/abs/1508.03273 — relative-phase Toffoli (`RCCX`) compute/uncompute identities reducing T/CNOT and ancilla overhead (Pattern C).
6. **Gidney (2019)**, *Windowed quantum arithmetic*, https://arxiv.org/abs/1905.07682 — QROM table-lookup windowing to merge sequential controlled arithmetic steps into lower-Toffoli blocks.
7. **Kissinger & van de Wetering (2020)**, *Reducing the number of non-Clifford gates in quantum circuits*, *Phys. Rev. A* 102, 022406, https://arxiv.org/abs/1903.10477 — ZX-calculus phase teleportation / gadgetization for ancilla-free non-Clifford gate cancellation.
8. **Heyfron & Campbell (2018)**, *An Efficient Quantum Compiler that reduces T count* (TODD), *Quantum Sci. Technol.* 4, 015004, https://arxiv.org/abs/1712.01557 — signature-tensor optimization of phase polynomials (applicable to merged nonlinear blocks in 36Q charts).
9. **Amy, Maslov, Mosca (2014)**, *Polynomial-time T-depth Optimization of Clifford+T circuits via Matroid Partitioning* (`t-par`), *IEEE TCAD* 33(10):1476–1489, https://arxiv.org/abs/1303.2042 — phase-polynomial matroid partitioning for space–time tradeoffs.
10. **Vandaele, Martiel, Goubault de Brugière (2022)**, *Phase polynomials synthesis algorithms for NISQ architectures and beyond*, *Quantum Sci. Technol.* 7, 045027, https://arxiv.org/abs/2104.00934 — low-CNOT phase-polynomial synthesis for affine/nonlinear chart boundary transforms.
11. **Seidel et al. (2024)**, *Qrisp: A Framework for Compilable High-Level Programming of Gate-Based Quantum Computers*, https://arxiv.org/abs/2406.14792 — high-level automatic uncomputation and dynamic qubit-lifecycle recycling.

### Retained Prior Literature from PR #29 (V4), PR #31 (V5 Atlas), PR #32 (V5 Shared-Lifetime)
12. Shirobokov et al. (2026), `arXiv:2611.09822` (DeepMind Lean formal quantum programs)
13. Ichikawa et al. (2025), `arXiv:2503.09356` (QAOA combinatorial search / parameter transfer)
14. Gidney (2018), `arXiv:1709.06648` / `Quantum` 2, 74 (Halving the cost of quantum addition)
15. Cuccaro et al. (2004), `quant-ph/0410184` (Ripple-carry addition)
16. Luongo et al. (2024), `arXiv:2407.20167` (Measurement-based uncomputation for modular arithmetic)
17. Paradis et al. (2024), `arXiv:2212.10395` / `Quantum` 8, 1258 (Reqomp)
18. Yang & Yuan (2026), `arXiv:2611.02345` (MBUndo)
19. Jeon, Huang, Cai (2026), `arXiv:2609.31605` (Measurement-Based Uncomputation from an Error Correction Perspective)
20. Bennett (1989), `doi:10.1137/0218053` (Time/Space Trade-Offs for Reversible Computation)
21. Ding et al. (2020), `arXiv:2004.08539` (SQUARE)
22. Paradis et al. (2021), `doi:10.1145/3453483.3454040` (Unqomp)
23. Meuli, Soeken, De Micheli (2022), `doi:10.1038/s41534-021-00514-y` (XAG)
24. Häner & Soeken (2022), `doi:10.1145/3501334` (ESOP cuts / T-depth)
25. Venev et al. (2024), `arXiv:2406.14227` (Modular uncomputation IR)
26. Ruiz et al. (2024/2025), `arXiv:2402.14396` (AlphaTensor quantum circuit optimization)
27. Zhang, Li, Ying (2025), `doi:10.1109/TCAD.2025.3570608` (Divide-and-conquer pebbling)
28. Amy & Lunderville (2025), `doi:10.1145/3704873` (Linear & non-linear relational analyses)
29. Xu et al. (2023), `doi:10.1145/3591254` (QUESO)

## 4. Next Integration Steps Across Sessions
1. **Replace single-stage V3/V4 macros on the period-112 7-bit rows (`8099..9014`) and 19–21-bit ripple chains (`7706..8032`, `9526..10185`)** with **Pattern A2 (Hybrid Gidney–Cuccaro/Takahashi)** macros so each 37Q peak bit costs `+1 CCX` instead of `+2` (V4) or `+4` (V3), while covering the 19 unresolved carry stages without context search.
2. **Cluster PR #29's 21 quadratic contexts by shared degree-2 factor** to apply **Pattern B (`m + 2` CCX)** on overlapping spans.
3. **Apply SAT-based width-36 pebbling (Meuli et al. 2019) + conditionally-clean borrowing (Khattar-Gidney 2025)** to the remaining long 37Q plateaus (`[57893, 60664]`, `[30051, 31170]`, `[33035, 33960]`) to push 36Q coverage from 87.54% toward 100%, then validate with full BDD equivalence and the official GVQCC `invsqrt` verifier.
