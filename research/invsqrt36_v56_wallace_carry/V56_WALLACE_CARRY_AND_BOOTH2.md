# V56: Multi-Stage Integer-Carry Wallace Tree (Real Native KMB + Gidney HMR) & Radix-4 Booth-2 Solution to PR #132's Multiplier Bottleneck (NOT SUBMISSION)

> **Stacked on PR #132** (V55 Radix-4 Global Tensor) and integrated with **PR #130** (V55 Fourier Tensor + 1-stage integer angle carry) and **PR #123** (V54 Deep Affine `-18.02%` ops + 60 Abel-chained syndrome hubs + Marginal Width-Tax Theorem).
> **Main and Kaggle untouched.** No official score claim yet; clearly separates verified real `.kmb` circuits (`n=7`, `n=15` multi-stage carry trees) from PR #132 end-to-end arithmetic budget integration.

---

## 1. Real Native `.kmb` Multi-Stage Integer Carry (`n -> floor(log2 n) + 1` Rotations, Zero-CCX HMR Uncompute)

Generalizes PR #130's 1-stage `3 -> 2` integer carry (`a + b + c = (a^b^c) + 2 maj(a,b,c)`) to **arbitrary-depth multi-stage Wallace trees**:

$$\sum_{j=1}^{n} f_j(x) = \sum_{k=0}^{\lfloor \log_2 n \rfloor} 2^k b_k(x)$$

using Gidney's **1-CCX `3:2` full-adder compressor** (`arXiv:1709.06648`) and **ZERO-CCX `HMR` measurement-based uncomputation** (all phase debts cancelled identically by classical-controlled Clifford `Z`/`CZ`).

Both circuits below were compiled to real binary `.kmb` via `kickmix`, re-read from disk, and **exhaustively verified over all $2^n$ inputs** for exact state restoration, **identically zero independent HMR phase debt**, and exact phase `popcount(x) * base_angle`:

| Native `.kmb` Circuit | Input Rots `n` | Output Rots | Rots Saved | Width `Q` | CCX | HMR | Total Ops | Exhaustive `2^n` + HMR | Net Gain (`7` Toff/rot) | SHA256 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: | :--- |
| `v56_multistage_carry_n7.kmb` | `7` | `3` | `-4` | `11` | **`4`** | `4` | `67` | **PASS (`128/128`)** | **`+24.0`** | `cdaa261ad76fccf4...` |
| `v56_multistage_carry_n15.kmb` | `15` | `4` | `-11` | `26` | **`11`** | `11` | `180` | **PASS (`32,768/32,768`)** | **`+66.0`** | `9171ad08090f3901...` |

---

## 2. Solving PR #132's `6,998`-CCX Truncated Multiplier Bottleneck (`32.7x` Reduction on Stage 1!)

On PR #132's exact 24-segment quartic specification (`v55_radix4_core.py`, **exact SHA256 `51e4370ddd9b1029b69163aca604697c2b0130da63e9c49b774c6a61d47d9477`**, `969` partial products, all `3,133,452` legal inputs PASS):

| Horner Stage | `av` Bits | Partial Prods | V56 Wallace `3:2` + CPA | V56 Gidney CAdd | **V56 Radix-4 Booth-2 CAdd** |
| :---: | :---: | ---: | ---: | ---: | ---: |
| `j = 3` (Stage 1) | `18b` | `153` | `312` CCX | `306` CCX | **`214` CCX** *(vs PR #132's `6,998` = **`32.7x` smaller!**)* |
| `j = 2` (Stage 2) | `22b` | `221` | `447` CCX | `442` CCX | **`286` CCX** |
| `j = 1` (Stage 3) | `25b` | `272` | `549` CCX | `544` CCX | **`340` CCX** |
| `j = 0` (Stage 4) | `28b` | `323` | `652` CCX | `646` CCX | **`394` CCX** |
| **ALL 4 STAGES TOTAL** | — | **`969`** | **`1,960` CCX** | **`1,938` CCX** | **`1,234` CCX** |

### End-to-End `33Q / 34Q` Budget with PR #132's Verified Native Components
- PR #132 measured radix-4 normalizer (`32Q`): `173` expected paid
- PR #132 quantized 24-segment loader (`33Q` / `34Q`): `484` / `444` CCX
- `31` generic rotations: `~225` Toffoli-equiv
- **+ V56 Booth-2 CAdd (ALL 4 quartic stages)**: `1,234` CCX
- **Total at `33Q`**: `C = 2,116.0` -> **`Q * C = 69,828.00` (only `+14.61%` above `60,927.56`!)**
- **Exact path to `< 60,927.56` (`C < 1,846.3` at `33Q`, needing `-270` CCX)**:
  1. **Windowed Arithmetic (Gidney `arXiv:1905.07682`)**: fuse `j = 3` (`214` CCX) directly into the QROM lookup table, OR switch from `deg = 4` (4 multiplies) to `deg = 2, b = 6` (`128` segments, only 2 multiplies!).
  2. **Radix-8 Booth-3 recoding** on `t` (`17` bits -> `6` signed digits instead of `9`).

---

## 3. Lean 4.35.0 Formalization & Reproducibility
- **Lean module**: `research/invsqrt36_v56_wallace_carry/lean/V56WallaceCarryTensor.lean` (`import Init`, zero Mathlib, proves `wallace_3to2_exact`, `hmr_maj_phase_cancel`, `wallace_7to3_multistage_exact`, `booth2_radix4_exact`, `multistage_carry_net_toffoli_gain`).
- **Executable compiler & receipt**: `v56_wallace_carry_save_compiler.py` and `v56_wallace_carry_receipt.json`.
- **OpenAI `corcondor/math` (`3344da59991e`) references**: `IntegralTensorBound.lean` (`integralTensorProducts`), `repair.tex` (`thm:repair`), `core-width.tex` (`lem:core-width`), `shaving.tex` (`lem:table-descent`), plus Gidney (`arXiv:1709.06648`, `arXiv:1905.07682`) and Kivlichan et al. (2020) Hamming-weight phasing.
