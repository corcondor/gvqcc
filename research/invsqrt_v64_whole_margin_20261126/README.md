# V64 whole-oracle absolute-margin transport — NOT SUBMISSION

Replayed PR #136 and #142 parents and six complete candidates, no new 37Q circuit. PRs #156/#158/#159 still do not contain a complete physical low-rotation Horner oracle; do not add their snapshot costs to the numbers below.

| Candidate | Q | CCX | Generic rotations | Operations | Independently computed official-formula cost |
|---|---:|---:|---:|---:|---:|
| PR136 parent | 36 | 1805 | 8541 | 75244 | 2554441.0652368185 |
| V64 margin + basis transport | 36 | 1382 | 7873 | 53605 | 2339847.7048538406 |
| PR142 parent | 25 | 5234 | 8280 | 89392 | 1858662.922085279 |
| V64 hybrid | 25 | 4992 | 7797 | 61955 | 1699410.3578343268 |
| V64 hybrid | 26 | 4524 | 7762 | 62934 | 1747684.3769661046 |
| V64 hybrid | 32 | 2368 | 7762 | 59481 | 2082004.156265975 |
| V64 hybrid | 35 | 1953 | 7762 | 56750 | 2262667.04591591 |
| V64 hybrid | 36 | 1837 | 7762 | 55683 | 2323138.6757992217 |

All re-read serialized KMBs passed full 4194304-input control and restoration replay, individual symbolic HMR debts, exact modular uint128 phase contraction and 3133452 legal tolerance checks. New plan differs from parent phase within allowed error. Actual minimum official integer margin 138112200; fixed floor 138111932. 36Q final SHA256 0cac7dac6f69a20bc0a026013a76659a789eef66f9e7e925d648c0a529568fb0; 25Q final SHA256 16bf345953456f61ed61917c635ccb732977a98e798a7670e017a8c4ff1ffe9d.

Methods: exact GF(2) span intersection for conditional products, retain intersection via CNOT basis changes, measured erase old complement, generate new complement; 262 nonliteral shared directions and 63 basis changes in best CCX 36Q. All 56 dyadic regions undergo 8 cycles of integer coefficient shrink/center and two-coordinate deletion/repair (7427->6876 cosets) under absolute-margin and analytic tolerance constraints. Whole-circuit cancellation removes 7337 X/CX pairs in 36Q, 9848 in 25Q. Three general affine frame policies tried but lost. A lower-margin 1539 CCX /8344 R candidate rejected (cost2563153.0664). Q25/Q26 have insufficient cache for intersection transport; improve through coefficient plan and routing/cancellation. Q32+ hybrid uses intersection transport. No physical splice of PR156/158/159 partial Horner circuits. These are full spectral approximate-phase circuits, not a solved low-rotation arithmetic evaluator.

Archive: GVQCC_V64_WholeOracle_MarginTransport_NOT_SUBMISSION.zip (103 files, 5210002 bytes, SHA256 2db864c0b98454bb1944e682b0597d23709b8fbcea5b04fa6c9f5e3bb55e1302), separately delivered in research conversation. Full runnable compilers, KMBs, plan/assignments, phase tags, independent replay and formula cost scripts, receipts, SHA256SUMS. Reproduce with bash reproduce.sh; requires Python/numpy/scipy/numba and g++ C++17. This PR contains compact core and local Lean identities only. Python 1000 exact random span and CNOT tests plus exhaustive Boolean identities passed locally. Lean execution not locally available; workflow configured; not a full native semantic Lean proof.

Literature: Amy & Lunderville POPL 2025 https://doi.org/10.1145/3704873 (relation-aware folding); Chen et al. https://arxiv.org/abs/2506.20624 (multi-block parity optimization); Gidney https://arxiv.org/abs/2507.23079 (constant workspace adder; carry perspective). This is an adaptation of mathematical ideas, not a direct implementation of those algorithms.

Best Q25 costs ~27.89 times competitive incumbent 60927.56. Thousands of generic rotations remain. No official KickMix, no competitive score improvement, no main/Kaggle changes.