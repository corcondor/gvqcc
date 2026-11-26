# V82 — two-sided parity-frame transport (research only)

Parent: PR #171 (V81 finite-field additive scan), exact source commit d442f72507472f5d4e1bce77a07f08ab1da2b16f. Public portfolio context: [Alex Chilton's notebook](https://github.com/corcondor/gvqcc/blob/main/references/kaggle/alexchilton/33-25-lb-which-circuits-survive-private-salt.ipynb). No competition binary was embedded in that notebook.

For y <- y + M x over GF(2), choose reversible elementary source and destination bases S,D, then implement (Sx,Dy), Dy <- Dy+(D M S^-1) Sx, and undo both frames. Optimize weight(D M S^-1)+2(length(S)+length(D)). The parent is included in every candidate set. All 4095 nonzero field scalar multiplication matrices checked using exact 24-dimensional symbolic replay; five seeded neutral-move searches plus both one-/two-sided greedy alternatives. This is a local heuristic, not an optimality proof.

| Native KMB | Q | CCX | HMR | CX | Instructions |
|---|---:|---:|---:|---:|---:|
| V81 reproduced | 851 | 45045 | 45045 | 2775524 | 3026775 |
| V82 | 851 | 45045 | 45045 | 2645716 | 2896967 |

129808 fewer CX/instructions, 4.2887% fewer instructions. Parent SHA256 ec3f2adcae920dcafcba0810d12e0a9b09b56df7a0feb4678159108067a3f252 (exact match PR171). Candidate SHA256 8d7ed6312e58508b186fd1fcbad24dafee8469eba96f9e03a5230fc542cb98f2. Independent local Python binary replay: all 4095 nonzero evaluation points, arbitrary coefficient affine maps, exact structural cancellation for every HMR outcome, restoration, 64 independently generated packed sparse-error instances with zero phase/value errors; mean paid 44331.03125 in these fixtures. Not official verifier.

Reproduction (from repository root):
```sh
python research/v82/v82.py parent parent.kmb
python research/v82/v82.py dual dual.kmb
sha256sum parent.kmb dual.kmb
cd research/v81
g++ -O3 -std=c++17 check_scan.cpp -o check_scan
python3 fixture.py
./check_scan ../../dual.kmb fixture.bin
```

The independent Python checker and serialized KMB are included in the V82 reproduction archive delivered in chat. The C++ checker above is the unchanged PR171 verifier; not re-executed in this session. The input ABI is (P,V), not competition syndromes. No complete DQI replacement, Q/paid-gate saving, official score improvement, Lean compilation, or competition submission claimed. The competitive branches and main circuit files are unchanged. References: Gao–Mateer additive FFT (2010), and the field/trace and recurrence references in PR171.
