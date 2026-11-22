# 2026-11-23 k8 global nonlinear synthesis: executed results

**Result: 0 scored improvement.** Public V8 k8 remains 211 Toffoli / 128Q. Independent full-table synthesis generated 14 radically different KMB implementations, with 14 workspace-allocated versions (28 fresh programs), plus 5 exact global cache-basis recompilations of the public 211T circuit. All **33 real KMBs** passed custom exact checks on all 1,219 legal address rows in forward and reverse, with all scratch=0 and symbolic HMR-phase cancellation. The **28 from-scratch circuits** further passed all **2,048** address bit patterns and arbitrary incoming word-register values (guaranteed structurally: word register never used as control). Both intentional phase/output mutations were correctly rejected. **This is not the unchanged official Kickmix verifier**, and no Kaggle submission was performed.

## Full nonlinear synthesis and actual KMB cost, k8

| Architecture | T | Q after liveness allocation |
|---|---:|---:|
| direct reversible 11-bit equality QROM | 24,380 | 56 |
| 4+7 hierarchical minterm QROM with HMR | 1,729 | 77 |
| low3/4/5/6 ANF | 2,146/1,628/1,430/1,397 | 58/64/78/108 |
| GF(2) high-output matrix factorization (m5/m6) | 1,136/1,453 | 115/126 |
| 3-way high-low-output tensor m5 | 1,494 => 1,276 after global basis search | 115 |
| **3-way tensor m6** | **768 => 681 after global basis search** | **126** |
| published specialized maoxin123 k8 | **211** | 128 |

The tensor compiler uses 57 low-variable AND monomials, 20 persistent reversible high-address equality predicates, and a multi-output product basis. A global GL(20,2) cache basis search (multiple re-basin random starts, greedy GF2 rank factorization) reduced the tensor rank sum **571 -> 484**, so measured Toffoli **768 -> 681** (197 setup AND cost + 484 bilinear products). These are real generated KMB costs, not a proxy for score; 681 is worse than 211. A 462-partition address-axis audit found 28 feasible under this 128Q persistent layout; the chosen contiguous split was best among those.

**Global cache/tail recompilation:** 5 additional distinct 211T KMBs generated using invertible GF(2) transformations of the public 82 cache values and automatic rewriting of every cache read across a 23,088-instruction output window. Contains 8, 32, 96, or 192 shear operations depending on candidate. This changes the cached Boolean *basis* but **does not introduce new ANDs or lower T**. All tested reachable rows and HMR symbols pass. It is a starting scaffold, not the missing new-product optimizer.

## The remaining research problem

The noncompetitive 681T compiler ignores the exact 82 specialized cached nonlinear products and prior angle-word state which the public 211T circuit exploits. The next genuine score-improving compiler must replace **nonlinear AND products outside the old cache's GF(2) span**, jointly resynthesize the 129-term output tail, allocate <=128Q and verify value+phase. The current source provides end-to-end KMB generation, liveness allocation and exact custom verification to run this work, but does **not** yet solve the public-cost problem. No optimality claim.

Full tested source, 33 KMBs, 2048-row and 1219-bidirectional receipts, two negative tests, SHA256 manifest, and unexecuted Kaggle official-evaluation notebook are in the chat attachment `GVQCC_GLOBAL_SYNTH_MULTIPATTERN_20261123.zip`. Run `bash RUN_ALL.sh` after extraction; the source tree was rerun from a separate directory and the best KMB SHA reproduced byte-for-byte:

`a195b552c6bbc7c9fe5a6029ebcdf5aafae5fa0985ffb64851f3e9f125dc53cb` (681T/126Q).

Public k8 fingerprint: `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`. Sources/credits in bundle.