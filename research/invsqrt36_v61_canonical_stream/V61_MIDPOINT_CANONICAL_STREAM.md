# V61: Hidden Midpoint Symmetry (`deg=3`/`deg=2` via 1 Free `X` Gate) & Real Native Canonical Bit-Serial Phase-Streaming Transducer (`<= 31` Rotations) (NOT SUBMISSION)

> **Stacked on PR #141** (V59 Packed Normalization + 132-CCX Canonical Transducer) and integrated with **PR #139** (V56 Wallace Carry + Booth-2), **PR #132** (Radix-4 Tensor), and **PR #123** (V54 Deep Affine + Marginal Width-Tax Theorem).
> **Main and Kaggle untouched.** Separates verified real native `.kmb` circuits (`B=6` exhaustive `4,096/4,096` PASS, `B=31` compiled & round-trip verified) and exact `3,133,452`-input integer polynomial audits from full-oracle submission claims.

---

## 1. Root Cause of the V58–V60 Wall (`457–707` Rotations) — And How V61 Breaks It

Direct inspection of the `37Q` incumbent (`invsqrt_v54_deep_affine_central.kmb`, lines `10813..11276`) reveals that it achieves `33` generic rotations (`240.38` Toffoli-equiv) by **NEVER applying `Z_POW` to intermediate partial products or carry-save digits**; instead it streams canonical output bits $y_k$ onto `q6`/`q29` one bit at a time with `Z_POW(-2^{-k})`.

V58–V60 (PR #140, #143, #144, #145) hit a hard wall at `457–707` rotations (`3,327–5,147` Toffoli-equiv from rotations alone, `> 1.86x` the entire `34Q` budget).

**V61 solves BOTH halves simultaneously:**

### (A) Real Native `.kmb` Canonical Bit-Serial Phase-Streaming Transducer (`<= 31` Rotations on 1 Qubit!)
Given any carry-save pair $(A, D)$ of width $B$, `CanonicalBitSerialPhaseStreamer` computes $y_k = A_k \oplus D_k \oplus c_k$ **one bit at a time onto ONE reusable qubit `q_rot`**, applies **EXACTLY $B$ `Z_POW` rotations**, advances $c_{k+1} = \mathrm{maj}(A_k, D_k, c_k)$ in `1` CCX, and uncomputes the entire carry chain in reverse using **ZERO CCX (`HMR` + Clifford `Z`/`CZ`)**:

| Real Native `.kmb` | Precision `B` | Rotations (on `q_rot`) | CCX | HMR | Total Ops | Verification | SHA256 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `v61_canonical_stream_b6.kmb` | `6` | **`6`** | **`5`** | `5` | `95` | **PASS (`4,096/4,096` exact + zero HMR debt)** | `a0ac8ef0bb14e9cd...` |
| `v61_canonical_stream_b31.kmb` | **`31`** | **`31`** | **`30`** | `30` | `595` | **Compiled & round-trip verified via `kickmix`** | `9e36cb564d58879e...` |

### (B) Hidden Midpoint Symmetry ($u = t - 2^{t_{\text{bits}}-1}$ via 1 Free `X` Gate) Across ALL `3,133,452` Legal Inputs
Flipping the MSB of the local mantissa offset $t$ (`1` free `X` gate!) centers $u \in [-h/2, +h/2)$, shrinking $|u|^3$ by **`8x`** and $|u|^4$ by **`16x`**, eliminating 1–2 entire Horner multiplication stages at `B35` (`32` canonical rotations):

| Degree `d` | Segments | `t` Bits | Violations (`3,133,452`) | `max(err/tol)` | Partial Products | Booth-2 CCX | Canonical Rots | `33Q` Projected `Q * C` (w/ PR #141 `169` norm + `30` stream) |
| :---: | :---: | :---: | :---: | :---: | ---: | ---: | :---: | :--- |
| `4` (PR #132 ref) | `24` | `17b` | `0` (PASS) | `0.9321` | `969` | `1,234` | `31` | `70,708.4` (`+16.05%`) |
| **`3` (V61 Cubic)** | **`48`** | **`16b`** | **`0` (PASS)** | **`0.7559`** | **`696`** | **`816`** | **`32`** | **`58,111.7` (`-4.62%` BEATS `60,927.56`!)** |
| **`2` (V61 Quadratic)** | **`192`** | **`14b`** | **`0` (PASS)** | **`0.8618`** | **`406`** | **`476`** | **`32`** | **`52,534.7` (`-13.78%` BEATS `60,927.56`!)** |

- `deg=2, 192 segs` (`406` partial products) uses **more than `2x` fewer partial products than PR #141's `845`**, with only **2 multiplications total** (`476` Booth-2 CCX)!

---

## 2. Lean 4.35.0 Formalization & Reproducibility
- **Lean module**: `research/invsqrt36_v61_canonical_stream/lean/V61CanonicalStream.lean` (`import Init`, zero Mathlib, proves `midpoint_shift_msb_free_x`, `canonical_stream_step_exact`, `canonical_stream_hmr_exact_cancel`, `v61_midpoint_beats_37q_budget`).
- **Executable compiler & receipt**: `v61_midpoint_canonical_stream.py` and `v61_midpoint_canonical_receipt.json`.
- **References**: Gidney (`arXiv:1709.06648`, `arXiv:1905.07682`), Häner–Roetteler–Svore (`arXiv:1805.12445`), Ercegovac & Lang (*On-Line Arithmetic*), plus `corcondor/math` (`3344da59991e`: `repair.tex`, `core-width.tex`, `shaving.tex`, `IntegralTensorBound.lean`).
