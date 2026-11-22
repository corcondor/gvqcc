# ANGLE multi-form synthesis ledger (v2, 2026-11-23)

This directory is a **versioned, append-only research data ledger**, not a verified Kaggle submission.

- `experiments.jsonl`: 240 records = 4 NPZ seeds × 4 synthesis methods × 15 slots. Each record includes source NPZ SHA-256, full compiler script SHA-256, stable experiment ID, Q, X/CX/CCX, all-valid-address logical proof status, and sample KMX SHA.
- `summary.json`: per-input, per-method totals and compiler SHA.
- `comparisons.csv`: exact CSV exported from the run (no extra index column).
- `all_kmx_manifest.json`: SHA-256 and gate counts of all 240 concrete KMX files in the linked local research bundle.
- `SHA256SUMS_CURRENT`: SHA-256 for local code, seeds, ledger and KMX files.

[Compiler](../../../../multi_angle_synthesis.py) · [Exporter](../../../../export_all_kmx.py) · [Tests](../../../../test_multi_angle_synthesis.py) · [Japanese analysis](../../../../2026-11-23_multiangle_results.md)

Reproducibility:
- Real-input Python bitparallel all-address oracle checks passed for all 240 circuits. Dirty target independence, unchanged tags and clean scratch were checked. X/CX/CCX only: no relative phase operations.
- GitHub Actions additionally checks native KickMix parsing and KMX→KMB roundtrip on small **synthetic** fixtures; this does **not** mean official verifier PASS for the real experiments.
- v1 is preserved under the parent directory: its sample KMX hashes came from an earlier header-order emitter. It must not be compared byte-for-byte against the present compiler. v2 records the exact compiler SHA to prevent accidental mixing.
- No new competitive KMB, no new score, and no demonstrated gain from the two-word C45 mutation.

Research code and ledger are public; the original large input NPZs and all 240 generated KMX files are packaged separately with the user-facing ZIP, not copied into GitHub.
