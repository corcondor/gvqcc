# V64: Controlled-Addition Post-Update Majority Transport (Zero-CCX HMR Erasure), `288`-CCX Real Native KMB for PR #147's 16-Digit Successor MAC, and Cross-Domain PR #154 Sign-Gauge QROM Compression (NOT SUBMISSION)

> **Stacked on PR #147** (V62 Live Horner: `36Q E928` / `35Q E1132`) and integrated with **PR #152** (V63 Rolling Phase Digits / $\Delta F$ differential transport), **PR #154** (Chemistry V65 exact GF(2) sign-gauge), and **PR #146** (V61/V62 Midpoint Symmetry + `4×8b` `33Q`-fit `32`-rotation canonical phase stream).
> **Main and Kaggle untouched.** Separates exhaustively verified real native `.kmb` engines (`1,024/1,024` exact + zero HMR debt; `W=17 × D=16` compiled & round-trip verified) from full-oracle official verification.

---

## 1. New Mathematical Identity: Controlled-Addition Post-Update Majority Transport (Zero-CCX HMR Erasure)

In a controlled-addition `d += ctrl * s` where uncontrolled carries `cout = maj(s, d, c)` are computed first and the sum update `d' = d ^ (ctrl && (s ^ c))` is applied top-down, the pre-update majority satisfies the exact identity (`controlled_add_post_update_maj_transport`, Lean 4.35.0 proven):

$$\mathrm{maj}(s, d, c) = \mathrm{maj}(s, d', c) \oplus \bigl(\mathrm{ctrl} \land (s \oplus c)\bigr)$$

Because the correction term `ctrl && (s ^ c)` is quadratic, measuring `cout` via `HMR cout -> m` leaves a phase debt cancelled **identically by Clifford `Z`/`CZ` with ZERO CCX uncomputation** (`controlled_add_hmr_zero_ccx_cancel`) — cutting every `b`-bit controlled-addition to **`2*b - 1` CCX total**!

---

## 2. Solving PR #147's Remaining 16-Digit Successor MAC Bottleneck (Real Native `.kmb` Compiled!)

Compiled via `kickmix` and reloaded from disk (`v64_unified_live_horner_kmb.py`):

| Real Native `.kmb` | Dimensions | CCX | HMR | Total Ops | Verification | SHA256 |
| :--- | :---: | ---: | ---: | ---: | :--- | :--- |
| `v64_mac_schoolbook_w6d4.kmb` | `W=6 × D=4` | **`32`** | `14` | `202` | **PASS (`1,024/1,024` exact + 0 HMR debt)** | `d0f461fdae604de5...` |
| `v64_mac_booth2_w6d4.kmb` | `W=6 × D=4` | `43` | `11` | `230` | **PASS (`1,024/1,024` exact + 0 HMR debt)** | `7f60d8b4b9bfdc89...` |
| **`v64_mac_schoolbook_w17d16.kmb`** | **`W=17 × D=16` (PR #147 full scale!)** | **`288`** | **`136`** | `2,168` | **Real `.kmb` compiled & reloaded** | `475b1f6d25feee62...` |
| **`v64_mac_booth2_w17d16.kmb`** | **`W=17 × D=16` (PR #147 full scale!)** | `321` | `80` | **`1,907` (`-12.04%` ops!)** | **Real `.kmb` compiled & reloaded** | `79612722f6e7e464...` |

### Integrated Budget with PR #147 (`928` paid) + PR #146 (`32` rotations, `52` CCX)
- PR #147 live 17-bit Horner chart (`36Q`): `928` paid
- **V64 ALL 16 remaining digits (`v64_mac_schoolbook_w17d16.kmb`)**: **`288` CCX**
- **PR #146 `4×8b` 32-rotation canonical phase stream (`v62_chunked_stream_b32_4x8.kmb`)**: **`52` CCX** + **`32` rotations (`233` Toffoli-equiv)**
- **Combined `36Q` estimate**: `C = 1,501` -> **`36 * 1,501 = 54,036` (`-11.3%` below `60,927.56`!)**
- **Combined `35Q` estimate** (with PR #147's `1,132` compact variant): `C = 1,705` -> **`35 * 1,705 = 59,675` (`-2.1%` below `60,927.56`!)**
*(Budget projection combining verified partial KMBs; full-oracle official `verify_submission_invsqrt.py` remains the final gate.)*

---

## 3. Cross-Domain Unification: Applying PR #154's Chemistry GF(2) Sign-Gauge to InvSqrt QROM Tables

Applying PR #154's exact GF(2) sign-gauge `w' ^ w = s * ((-w) ^ w)` + Viterbi-optimal Abel differencing across PR #132's 24-segment coefficient table `C0..C4`:

| Coefficient | Bit Width | Raw Hamming Weight | Abel Diff Only | **Sign-Gauge + Abel Diff** | Reduction |
| :---: | :---: | ---: | ---: | ---: | ---: |
| `C0` | `33b` | `366` | `340` | **`300`** | **`-18.03%`** |
| `C1` | `29b` | `350` | `268` | **`260`** | **`-25.71%`** |
| `C2` | `26b` | `256` | `237` | **`211`** | **`-17.58%`** |
| `C3` | `23b` | `289` | `183` | **`163`** | **`-43.60%`** |
| `C4` | `19b` | `101` | `107` | **`98`** | **`-2.97%`** |
| **TOTAL** | — | **`1,362`** | `1,135` | **`1,032`** | **`-24.23%`** |

---

## 4. Lean 4.35.0 Formalization & References
- **Lean module**: `research/invsqrt36_v64_live_horner_hmr/lean/V64UnifiedDiffGauge.lean` (`import Init`, zero Mathlib).
- **Executable compiler & receipt**: `v64_unified_live_horner_kmb.py` and `v64_unified_live_horner_receipt.json`.
- **References**: Gidney (`arXiv:1709.06648`, `arXiv:2507.23079`), Khattar–Gidney (`arXiv:2407.17966`), PR #147, PR #152, PR #154, and `corcondor/math` (`3344da59991e`).
