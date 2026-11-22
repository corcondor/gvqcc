# GVQCC v4 experimental evidence (2026-11-23)

Scope: four existing public/derived angle tables, 13 parameterized compiler variants grouped into 3 algorithmic families, 780 concrete new KMX files. These produce **150 distinct SHA-256 circuit hashes**; unchanged variants are not counted as independent structural discoveries.

- [Experimental report](../../../../multiangle_v4/REPORT_JA.md)
- [Exact implementation](../../../../multiangle_v4)
- [Independent KMX gate-by-gate checks](independent_verified.jsonl): 780/780 PASS, all legitimate addresses and formal HMR coefficients; **not an official native KickMix verification**.
- [Aggregate counts](summary.json), [per-slot controlled ablation](per_slot_c46.json), [physics/reference metrics](physical_numerical_results.json), [parameter comparison](decision_matrix.json).
- [Independent exact DP matching certificate](matching_dp_independent.json): networkx result cross-checked with an independent 20-vertex bitmask matching search on all 4×15 slots.
- The full new KMX files and their manifest are supplied separately as a ZIP attachment; GitHub stores code plus measured ledger rather than 780 large plaintext gate files.

**Official full verifier, Kaggle submission, and new official score: not done.**
