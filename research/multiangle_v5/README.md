# GVQCC v5: fixed-high-factor matroid basis synthesis

Files and results are documented in [REPORT_JA.md](REPORT_JA.md). This is research on the structure of a generic 127-qubit 7-bit/J5 ANGLE compiler, **not a new competition score**.

## Reproduce from the attached four research seeds

Requires NumPy (and the archived local compiler sources in sibling directories). For exact numerical and bitset checks:

```bash
OPENBLAS_NUM_THREADS=1 python gvqcc_multiform_v5/test_high_group_basis.py -v
OPENBLAS_NUM_THREADS=1 python gvqcc_multiform_v5/high_group_basis.py \
  --seed gvqcc_multiform/seeds/c46_public_v8.npz \
  --out output/c46-upper8 --axis fixed-upper --max-support 8 \
  --global-mode canonical --emit
OPENBLAS_NUM_THREADS=1 python gvqcc_multiform_v5/global_20_basis.py \
  --seed gvqcc_multiform/seeds/c46_public_v8.npz \
  --out output/c46-cross20 --max-support 3 --emit
OPENBLAS_NUM_THREADS=1 python gvqcc_multiform_v5/verify_all.py
OPENBLAS_NUM_THREADS=1 python gvqcc_multiform_v5/run_matrix_24.py \
  --seeds gvqcc_multiform/seeds --out output/matrix24
```

`verify_all.py` reads the archived four output directories under `gvqcc_multiform_v5/` and writes the independent serialized-KMX proof, not native KickMix shots. The test suite optionally imports KickMix and checks three C46 generated KMX→KMB roundtrips when the wheel is installed. For Github Actions, those tests are not skipped.

## Artifact structure

- `gvqcc_multiform_v5/high_group_basis.py`: 1,2,3,...,8-state candidate basis with GF(2) inverse and constructive KMX;
- `gvqcc_multiform_v5/global_20_basis.py`: cross-axis selector rank-aware alternative, measured worse (negative evidence);
- `group_screen_24.jsonl`: 4 angle-table sources × two group directions × support sizes 2,3,8;
- `independent_60_verified.jsonl`: 60 emitted KMX (4×15), all-address bitparallel, phase and scratch checks;
- `global20_independent_30.jsonl`: 30 emitted KMX (two support sizes×15), negative result;
- `run_c46_upper8/` etc: 60 concrete real KMX, each SHA fixed;
- `global20_c46_s2_emitted/`, `global20_c46_s3_emitted/`: 30 KMX and their source records;
- `gvqcc_multiform_v4/pinned_c46_words.py`: public data source for native smoke tests;
- `SHA256SUMS`: exact input and output hashes.

Main scientific conclusion is an **exact conditional minimum** inside a particular cofactor-group compiler class, not a global minimum of multiplicative complexity. More output sharing across unrelated high groups, or a different XAG emitter, lies outside the theorem.
