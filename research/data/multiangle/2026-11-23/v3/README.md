# GVQCC multiangle v3 experiment registry

2026-11-23. Versioned historical ledger: previous v2 records are unchanged.

- Four NPZ sources and **35** synthesis settings; **2100** exact output/circuit instances, 15 ANGLE loaders per setting and source.
- Eight separate HMR/affine and partition seed ledgers, plus the selected-wire-permutation ledger and per-run summaries.
- `ALL_KMX_SHA256_part1..4.jsonl`: every KMX SHA-256, source, method, slot, and size; the 4 parts together have 2100 unique rows. Full KMX source text is stored in the conversation ZIP, not in GitHub.
- `screen_c46_462.jsonl`: exhaustive evaluation of C(11,6)=462 wire choices for the fixed low6 basis compiler, using an **exact constructive CCX formula** that was independently confirmed on six selected wire choices and all real NPZ inputs.
- `MASTER_SUMMARY.json`: all 140 method/source groups and their static CCX, CX, HMR, width, and Q×CCX *proxy*. `FILE_INDEX_SHA256`: checksums of source, scripts, reports and index.

**No new official KickMix verification or Kaggle score.** Every conclusion must state its evidence tier: exact algebra/bitparallel oracle/HMR symbolic phase/native fixture parsing/official verification. Only the first three have full real-input evidence here.
