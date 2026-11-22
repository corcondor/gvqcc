# OSS chained-AND/CEGAR actual run (2026-11-23 JST)

Source: `manwithacat/vqcc-tools` v0.3.0, vendored unchanged under `third_party/manwithacat/chained_and.py`.
Fixture: `fixture_k8_4out_8rows.json`, SHA-256 `51cc120a925232f8aaa29863748bcd3524d7cc278fe6d8c8d3d5a0fe3ab7e672`.
CI proof: https://github.com/corcondor/gvqcc/actions/runs/45060321532
CI work SHA: `2480d0312f5204aea9169ff7c91a9358343e6895`
Evidence artifact: https://github.com/corcondor/gvqcc/actions/runs/45060321532/artifacts

## Upstream regression (unmodified)

Python 3.12, NumPy 2.1.3, Ubuntu 24.04 CaDiCaL 1.7.4 (apt package).
19 tests executed; **18 PASS, 1 SKIP**. SAT/CEGAR test `test_r7_cegar_with_solver` PASSED, confirming solver interface; the skipped `test_real_target` requires a separate extra target path.

## Real-data adapter

Target: bank k8, 8 rows of 16 addresses, 4 output bits, all 128 care points.
The original `construct_rank2` emitted **12 model ANDs** and passed all 8 rows modulo arbitrary output constants per row (part of model). Depth-1 lower bound for these output rows: **4 AND** (mixed affine rank 7). Both are formal small-window quantities; neither is a valid final KMB.

`encode_shape` with k=4, chained=1, 2 initial rows: **2,292 SAT variables / 7,684 clauses**.

CaDiCaL CEGAR (gauge+lex, force chained, timeout per iteration 8s, CPU budget 20s, max 5 iterations):
- iteration 0: 2 rows, 2,292 vars / 7,684 clauses, SAT in 0.008 CPU s; exhaustive 2/8 satisfied
- iteration 1: 3 rows, 3,168 vars / 11,013 clauses, SAT in 0.057 CPU s; exhaustive 3/8
- iteration 2: 4 rows, 4,044 vars / 14,342 clauses, UNKNOWN after 8.002 CPU s

**Final solver outcome: unresolved** (NOT UNSAT and NOT a valid all-8-row solution). CPU 8.07s. No k8 loader replacement emitted. No 128Q, measurement phase, or official KickMix proof; public score unchanged.

## Interpretation

The SAT encoding and upstream algorithm run on actual V8 data. However, solving a tiny four-output window already stalls at 4 rows for k=4 under these settings. Blindly applying global 35-output exact SAT would be irresponsible. The fastest path to an actual competitive KMB remains an OSS `qrom-plan` / `tensorqrom` constructive baseline with real emitted Q/T and HMR verification; use chained-AND optimization only where its measured model gain can survive those costs. All sources and licenses are in the PR README.
