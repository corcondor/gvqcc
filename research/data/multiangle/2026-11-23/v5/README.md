# v5 measured high-group basis study (2026-11-23)

**No official score update.** The exact mathematical claim is restricted to a fixed 6-low/5-high address split, a fixed upper one-hot factor, and this particular low-ANF multi-output emitter. In this class minimum-weight GF(2) vector-matroid greedy returns the minimum sum of additive CCX candidate costs. This does **not** prove global circuit or physical optimality.

- **Mathematical derivation and limits:** [../../../../multiangle_v5/REPORT_JA.md](../../../../multiangle_v5/REPORT_JA.md)
- **Sources:** [../../../../multiangle_v5/high_group_basis.py](../../../../multiangle_v5/high_group_basis.py), [../../../../multiangle_v5/global_20_basis.py](../../../../multiangle_v5/global_20_basis.py)
- **Full completed sweep:** [group_screen_24.jsonl](group_screen_24.jsonl), 4 input tables × fixed-upper/fixed-lower × support 2/3/8 = **24 configurations**, all 15 banks synthesized and symbolically tested; [group_screen_360_slots.jsonl](group_screen_360_slots.jsonl) has 360 per-bank receipts.
- **Emitted KMX serializations:** [independent_60_verified.jsonl](independent_60_verified.jsonl) and [independent_60_summary.json](independent_60_summary.json), 4 seeds×15 banks; [global20_independent_30.jsonl](global20_independent_30.jsonl), 2 cross-20 variants×15 banks. Each row includes serialized SHA256 and independent bitparallel all-address phase/scratch certificate.
- **Full reproducible ZIP**: GVQCC_20261123_v5_matroid_90KMX.zip (90 KMX, all four source NPZs, independent verifier, source compilers, archived v2-v4 dependencies, SHA256 manifest), SHA256 **b981d03b9a2e851d93f75c9df451ef49b3bf9bac0c48dfe1313cf304212db0e4**. The binary KMX and input seeds are not duplicated in GitHub. User-facing artifact uploaded in the same conversation.

**Numerical outcomes, CCX/pass, same 127Q:** public C46 9,607 (v4 pair) → 9,389 (support 2) → 9,381 (support 3) → **9,301 (support 8)**. C45/B129 10,588 (v4) vs 10,589; C45/B130 unchanged 10,708. Cross-20 basis support2=9,577 and support3=9,606 (negative).

**Evidence tiers:** constrained linear-algebra statement and m=3 independent brute-force; generated KMX+bitparallel all-address/relative phase; native KickMix KMX→KMB parsing only on pinned actual C46 when available; official complete KickMix verification **not performed**.
