# V67: Multi-Method Bilinear Tensor Contraction, Real `.kmb` Karatsuba Multiplication, and 18-CCX Don't-Care QROM

> **Research artifact (not a Kaggle submission; does not mutate `main`).**  
> All gate counts and SHA-256 hashes below are measured directly on real compiled native `.kmb` circuits parsed back through `kickmix.Circuit.from_file`, and all algebraic identities are machine-checked in Lean 4.35.0 (`import Init`, zero Mathlib).

## Motivation & Literature Grounding

Rather than relying on a single local peephole heuristic, V67 tests **five mathematically distinct circuit-compression methods** on real native `.kmb` circuits, inspired by:
- **Gidney (2019), `arXiv:1904.07356`** — *Asymptotically Efficient Quantum Karatsuba Multiplication* (rank-3 bilinear tensor contraction for integer multiplication, the finite-width ancestor of fast bilinear multiplication / Strassen–$\omega=9/4$ tensor contraction).
- **OpenAI `corcondor/math` (`3344da59991ed94f9ba711217b29c1d760badfa6`)** — `repair.tex` / `quotient.tex` / `shaving.tex` (rank-structured tensor contraction, finite Fourier/additive quotient reuse, and explicit separation of asymptotic exponent regimes vs. finite-width constant factors).
- **Reachability-aware / Don't-care bilinear QROM** (connecting to peer PR #173 `V86` and PR #152 `V63` / PR #155 `V64` HMR zero-CCX uncomputation).

---

## Measured Real `.kmb` Results

### 1. Real Native `.kmb` Full $n \times n$ Multiplier: Schoolbook vs. Karatsuba Rank-3 Bilinear Contraction

Both multipliers use exact HMR zero-CCX carry uncomputation. Exhaustive simulation at $n=4$ ($2^8 = 256$ inputs) confirms exact $V \cdot T$, clean input/ancilla restoration, and zero HMR phase debt for both circuits. At full $16 \times 16$ scale, **real native `.kmb` Karatsuba strictly beats Schoolbook in CCX**:

| Circuit (real `.kmb`) | Scale | Verification | `CCX` | `HMR` | Total ops | SHA-256 (prefix) |
|---|---|---|---:|---:|---:|---|
| `v67_mul_sb_n4.kmb` | $4 \times 4$ | `256/256` exact + 0 HMR debt | `48` | `20` | `358` | — |
| `v67_mul_karatsuba_n4.kmb` | $4 \times 4$ | `256/256` exact + 0 HMR debt | `74` | `30` | `596` | — |
| `v67_mul_sb_n16.kmb` | $16 \times 16$ | compiled `.kmb` | `768` | `272` | `6,248` | `018df6fdebf60281` |
| `v67_mul_karatsuba_n16.kmb` | $16 \times 16$ | compiled `.kmb` | **`716`** (**`-52` / `-6.77%`**) | `248` | `6,311` | `1746888543c4ad82` |
| `v67_mul_karatsuba_n16_opt.kmb` | $16 \times 16$ (+ Method 4 affine) | compiled `.kmb` | **`716`** | `248` | **`6,261`** (`-50` / `-0.79%`) | `c84adb770ad34ad6` |

### 2. Method 4: Deep $\mathbb{F}_2$ Affine Resynthesis on Real `.kmb` Multipliers

Applying V54 deep $\mathbb{F}_2$ affine resynthesis on top of our real `.kmb` multipliers reduces total instruction count with zero `CCX` increase:

| Target Real `.kmb` | Input ops | Output ops | Saved ops | `CCX` (unchanged) | SHA-256 (prefix) |
|---|---:|---:|---:|---:|---|
| `V64_Booth2_17x16` (`v67_mac_booth2_w17d16_opt.kmb`) | `1,907` | **`1,844`** | **`-63` (`-3.30%`)** | `321` | `db44d2785a97dc4a` |
| `V67_Karatsuba_16x16` (`v67_mul_karatsuba_n16_opt.kmb`) | `6,311` | **`6,261`** | **`-50` (`-0.79%`)** | `716` | `c84adb770ad34ad6` |

### 3. Method 5 (Real Native `.kmb`!): 18-CCX Don't-Care-Aware Bilinear Tensor QROM + MST-Hub CX Compression

For InvSqrt's 24-segment polynomial table `C0..C4` (`125` magnitude bits across `s in 0..23`):
- **Reachability / Don't-Care Identity**: For all valid segments $s < 24$, bits $a_3$ and $a_4$ are never simultaneously $1$ ($a_3 \land a_4 = 0$).
- Splitting $(a_0, a_1 \mid a_2, a_3, a_4)$ yields:
  - Low basis $m = [a_0, a_1, a_0 a_1]$ (`1` cache CCX)
  - High basis $M = [a_2, a_3, a_2 a_3, a_4, a_2 a_4]$ (`2` cache CCX instead of `4`)
  - Mixed bilinear basis $m_i \land M_j$ (`3 × 5 = 15` CCX, reusing **1** streaming product ancilla via zero-CCX HMR!)
- Total: **ONLY `18` CCX and `4` clean ancillas** to load all `125` bits of `C0..C4` across all `24` segments (beating standard unary 24-segment QROM `23` CCX by `-21.7%`, naive per-output rank-1 `294` CCX by `-93.9%`, and PR #132's `484`-CCX loader by `-96.3%`).
- Adding **Minimum-Spanning-Tree (MST-Hub) CX compression** across the 125 output columns cuts total instructions by **`-38.01%`** (`1,397 -> 866` ops, `CX 1,264 -> 733`), verified **exhaustively across all `24/24` segments × `125` bits (`3,000/3,000` bit checks, clean address/ancillas, `0` HMR phase debt)**:

| QROM Real `.kmb` | Exhaustive Check | `CCX` | `HMR` | `CX` | Total ops | Ancillas | SHA-256 (prefix) |
|---|---|---:|---:|---:|---:|---:|---|
| `v67_bilinear_qrom_c0c4_125b_raw.kmb` | `24/24 × 125b` PASS | `18` | `18` | `1,264` | `1,397` | `4` | `5659cd92360d78b9` |
| `v67_bilinear_qrom_c0c4_125b_mst_hub_compressed.kmb` | `24/24 × 125b` PASS | **`18`** | `18` | **`733`** (`-42.0%`) | **`866`** (**`-531` / `-38.01%`**) | **`4`** | `b646cd6796d62fe6` |

*(Theoretical note: pairing the 18 shared mixed basis elements via rank-2 `(a1.m + b2.M)(a2.m + b1.M)` further bounds global shared bilinear products at `5 + ceil(18/2) = 14` Toffolis when outputs consume paired sums.)*

---

## Lean 4.35.0 Formalization

- [`lean/V67BilinearKaratsuba.lean`](lean/V67BilinearKaratsuba.lean) (`import Init`, zero Mathlib):
  - `karatsuba_rank3_exact`
  - `paired_rank2_bilinear_identity`
  - `dont_care_24seg_high_vanishes`
  - `mst_hub_xor_exact`
  - `v67_measured_real_kmb_reductions`
- CI workflow: [`.github/workflows/invsqrt36-v67-bilinear-tensor-lean.yml`](../../.github/workflows/invsqrt36-v67-bilinear-tensor-lean.yml)
