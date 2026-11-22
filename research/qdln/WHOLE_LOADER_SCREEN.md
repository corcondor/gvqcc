# QDLN whole-ANGLE structural screen (no native KMB gain yet)

This follow-up distinguishes three quantities that must not be conflated.

1. Published V8 binary: 15 real ANGLE files have exactly **3,375 paid three-qubit operations per pass** by KMB v2 header counts. Batch costs: [246,241,218,218,218,241,218,241,213,218,218,241,218,213,213]. Their full qubit peak is 128 per loader.
2. Independent-output mixed-ANF synthesis: **3,850** paired bilinear core-product indicators (NOT complete Toffolis: ignores cached monomials and cleanup).
3. Exact invertible output XOR-basis optimization (pairwise greedy): **3,249** paired bilinear core-product indicators, a reduction of **601 indicators** relative to #2.

Per batch (baseline mixed-core -> XOR-basis mixed-core):
- 0: 280 -> 245
- 1: 280 -> 240
- 2: 245 -> 204
- 3: 245 -> 203
- 4: 245 -> 204
- 5: 280 -> 240
- 6: 245 -> 205
- 7: 280 -> 240
- 8: 245 -> 205
- 9: 245 -> 205
- 10: 245 -> 205
- 11: 280 -> 240
- 12: 245 -> 205
- 13: 245 -> 204
- 14: 245 -> 204

The pairwise changes preserve the GF(2) span of each set of 35 output functions exactly and are reversible by CNOTs. This **does not** prove that 3,249 Toffolis can implement the loaders, still less that it improves over 3,375: it excludes high/low monomial caches, output-basis restoration, word-register constraints, measurement-based cleanup, and 128Q scheduling. The current published compiler can do better through more extensive cross-output sharing and free incoming gauge sources.

In particular, local QDLN micro-oracle saving 6 -> 2 products on batch-2 row-58 is a true local improvement over a simple shared-ANF construction, but it does not subtract from the published 218 paid operations in the full batch-2 KMB.

## Mathematical direction for next step

Let C in GF(2)^(L x H x O) be the mixed low/high/address-output ANF tensor. A cached product gate can contribute (a1 outer b1 + a2 outer b2) outer s, where a_i are low-monomial parity vectors, b_i high-monomial parity vectors, and s is a shared output fanout mask. The full objective is:

    minimize K + cache_cost + measure_cleanup_cost

subject to exact equality of the entire tensor and every required reachable input/output and HMR phase branch, under Q<=128 per ANGLE circuit.

A differentiable neural search can propose (a1,b1,a2,b2,s) and multiple product sharing. Each discretized candidate must be checked exactly over GF(2), compiled to native KickMix, and verified under the actual full chemistry algorithm. This joint-product factorization, not single-output simplification, is the unfinished part.

No new KMB, hosted official PASS, Kaggle submission, or global score improvement has been recorded.
