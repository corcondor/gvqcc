# GVQCC Verification & Optimization Findings Report

## 1. Competition Scoring & Direction (Verified)
- **Kaggle Leaderboard Metric**: $\text{Score} = \left(\prod_{b=1}^{3} \frac{\text{cost}_b^{\text{ref}}}{\text{cost}_b}\right)^{1/3}$ (**Higher is better**).
- **Rank 1 (Public LB)**: `29.90871` (Entangled Team).
- **Current Team Best (Public LB)**: `27.30683` (`submission.zip`, Rank 355).
- **Latest Forked Public Frontier**: `maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry` (`27.31512`), combining:
  - `invsqrt`: `Q=46`, cost `78,673.57` (ratio `26.39736`)
  - `dqi`: `Q=889`, cost `360,209,905,486.02` (ratio `67.84784`)
  - `dfthcsos`: `Q=427`, `T=14,722`, `lambda_eff=46.9097`, cost `294,888,332.10` (ratio `11.37922`)

## 2. Reproducible Local Verification Results (WSL)
### A. `dqi` (`baseline_dqi.kmx`: `Q=889`, `52,930,180` ops)
- Gate counts (`scan_dqi.cpp`): `CCX=364,174`, `CCZ=7,000`, `CSWAP=12,240` (`383,414` Toffoli-like), `CX=31,293,631`, `CZ=538,972`, `HMR=71,568`, `R=48,012`.
- Built and verified a 0-ancilla `54-CCX` (`66-CCX` controlled) Karatsuba $\mathrm{GF}(2^{12})$ multiplier (`test_54ccx_gf2mul.py`, `verify_54ccx_gf2mul.py`: `0/2000` errors).
- **Why it did not reduce `baseline_dqi.kmx`**: Inspection of `baseline_dqi.kmx` (`inspect_dqi_block.cpp`) showed it already uses a **`42-CCX`** $\mathrm{GF}(2^{12})$ multiplier + `SWAP`/`HMR` measurement-based uncomputation, not `kickmix`'s `63-CCX` multiplier.
- Local commutation scan (`scan_dqi_ccz_cswap.cpp`, window=256): `0` `CCX`/`CCZ`/`CSWAP` cancellations, `0` `CCZ` merges, `96` `CCX` merges.

### B. `dfthcsos` (`angle_k_0..14.kmb`: `4,033 CCX` per pass, `Q_total=427`, `temporary_qubits=303`)
- Peephole scan (`check_ak4_peephole.cpp`): `0` `CCX` cancellations and `0` `CCX` merges across all 15 circuits (`ak0=291`, `ak1..3=286`, `ak4..14=261..263`).
- Fanout structure (`check_ak4_ccx_structure.py`): `106` (`ak0`) and `189` (`ak4`) output `CCX`s all have unique fanout masks (`0` duplicates), using `CX` feedback from output qubits into `q0..q3`.
- Continuous / fixed-`words0` `(W, H2_I)` optimization (`polish_strict_brot8.py`): pushing `lam_eff` to `43.999870` violated `err2 = 21.048 mHa > 20.0 mHa`; feasible points saturate near `lam_eff ~ 46.906`.
- Discrete `brot=8` `angle_words` perturbation (`test_lsb_block_flips.py`): even `K=1` single-LSB (`1/128`) perturbation on the highest-gradient entry raised `err1` from `19.9999 mHa` to `114.1228 mHa`.
- **Why `maoxin123` (`4,030 CCX`) works**: Instead of unconstrained post-hoc compression, `Coded Words` constrains `bit 0` (and batch XOR `bit 1, 2`) to low-degree Reed–Muller functions over `q0..q3` *before* refitting `(W, H2_I)`.

### C. `invsqrt` (`invsqrt.kmb`: `Q=46`, `T=1551`)
- Gate counts (`scan_invsqrt.cpp`): `CCX=1,413`, `CSWAP=129`, `CCZ=9`, `Z_POW=38`, `HMR=1,278`.
- Commutation scan (window=256): `0` `CCX` cancellations, `0` `CCX` merges.

## 3. Scope & Limitations (No False Optimality Claims)
- None of the above constitutes a mathematical proof of global optimality—indeed, `29.90871` on the leaderboard proves ~`1.314x` combined cost reduction beyond `27.30683` is achievable.
- Bridging `27.315 -> 29.9` requires structural/algorithmic changes rather than local peepholes:
  1. `dfthcsos`: reducing `inner_state_prep_temporary_qubits` (`303`) or changing DF-THC rank `(R, B)` / `brot`.
  2. `dqi`: reducing workspace qubits (`q840..q888`, `Q^2` scaling), `GF(2^{12})` / `GF(2^{24})` bilinear rank (e.g., Rank-173), or `Cutoff` vs $R(\epsilon_+)$ trade-off.
