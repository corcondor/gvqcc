# Credits & Notice (V69 Chemistry Loaders)

Lineage and attribution (preserve with any redistribution):

1. **Syed Asad Ali** — Original builder of the GVQCC circuit portfolio (Apache-2.0).
2. **maoxin123** — Chemistry angle words and 82-product wired angle-loader cache (table design by team ThemBones).
3. **goodpjw2008** — Sliding-window group-start loader method, refitted weights, and dead-cell zero-column method.
4. **PR #175 (`research/claude-chem3312`)** — 95-product frame-changed group-start loader pipeline (`d20.cpp`, `hsolve.cpp`, `phase1bs5.cpp`, `make2.py`) and wired planner (`planted_design.py`, `specgen.py`).
5. **V68 / V69 (this PR)**:
   - `v68_planted_allz3.py`: All-8,191 vectorized `z3` functional scan cracking Bank 14 at **207 Toffolis** (41-product planted Block 2 + 3 closers, `GVQ_SPECIAL=6,9`, official `dfthcsos/verify.py` PASS on both salts at `3,301` Toffolis/pass).
   - `run_v69_heads.ps1`: Zero-word-change 95-product head-loader rebuild (`k = 5, 7, 11` from `235 → 233`) on top of the verified `3,284` chemistry family (`lambda_eff = 46.914266`), achieving **`3,278` Toffolis/pass** (official `dfthcsos/verify.py` PASS on both salts).
