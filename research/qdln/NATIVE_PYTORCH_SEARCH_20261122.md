# QDLN native KMB + multistage PyTorch experiments — 2026-11-22

## Parent-preserving implementation

The new native_warmstart.py reads original KickMix v2 ANGLE KMBs. It preserves the first 82 cache-producing CCX operations as a physical feature bank. All later CCXs before the first HMR are represented by exact GF(2) control parities and propagated output fanout masks over the **actual 128 live wires**.

All 15 public V8 KMBs passed the symbolic extraction without dependence of a later AND control on a previous output-product result. An independent replay passed for **1,219 legal addresses × forward/reverse × 15 batches = 36,570** complete 128-qubit states at the first HMR boundary. No changed KMB, cleanup or phase score is claimed.

The new torch_multistage.py keeps the existing exact circuit as an immutable incumbent, with PyTorch straight-through hard forward: learnable input parity, output fanout and causal hidden-to-hidden XOR connections. The student is never promoted without exact discrete verification and downstream KMB checks.

## Actual published V8 cost audit

| Batch class | Indices | Native paid CCX | First HMR prefix | After first HMR |
|---|---|---:|---:|---:|
| Restart 0 | 0 | 246 | 109 | 137 |
| Restart 1 | 1, 5, 7, 11 | 241 each | 109 | 132 |
| Coded A | 2, 3, 4, 6, 9, 10, 12 | 218 each | 213 | 5 |
| Coded B | 8, 13, 14 | 213 each | 208 | 5 |

Every bank has 82 cache CCXs; the 15 published KMBs total **3,375 paid Toffolis per pass**. The scratch-from-zero proxy that gave 306 vs 246 for batch0 and 284 vs 218 for batch2 does not reproduce the published cache, output-register gauge or schedule. These are incomparable implementations, not proof that output grouping increases the optimal cost.

Pre-HMR linear-span checks of all 15 KMBs found zero individually removable CCXs. Exact source-feature extraction covered 1,295 paid products across ten coded batches. Each factor activation matched all 2,438 forward/reverse inputs. All pairwise cached-source polar-factor combinations failed to yield a rank-2 XOR pair: local two-product reuse is not the next lever.

## Rigorous local lower bounds

The alternating polar matrix B of a quadratic Boolean output obeys the multiplicative complexity lower bound AND_count >= rank_GF2(B)/2. Batch2 groups of 4, 8 and 16 actual cached-wire products each have output XOR witness ranks 8, 16 and 32, respectively. These independently sampled subgraphs saturate the lower bound under **full formal 128 cached-input equivalence**.

For broader selected groups, the proven lower-bound witnesses were: 32 products -> >=23, 48 -> >=30, 64 -> >=43, 96 -> >=49. These are lower bounds, not alternative constructions or reductions.

The post-cache wires in the real KMB are correlated on the legal address/gauge subspace. The formal-input lower bounds therefore do not rule out genuinely global redesign exploiting those correlations.

## PyTorch experiments (CPU, hard discrete checked)

- Single-level 16->15: 2 optimizer runs, no exact reduction.
- Single-level 32->31: 6 runs, no exact reduction.
- Single-level 64->63: 4 runs, no exact reduction.
- Two-level causal 16->15: 4 runs, no exact reduction.
- Two-level causal 32->31: 4 runs, no exact reduction.

The causal model learned hundreds of additional connections, but did not preserve the hard Boolean outputs after gate removal. Exact native gate reductions: **0**. The parent 3,375T baseline is unchanged. The comparison target for future integrated candidates is the newer public **3,372T per pass**, which was not resynthesized here.

## Next algorithmic direction

Replace unconstrained 128-feature straight-through gate toggles with constrained tensor-factor proposals and exact GF(2) projection. Optimize 32–128 products and the existing cache/gauge/bank scheduling together; allow intermediate nonlinear features, output-basis transforms and signed top-bit gauge. Preserve the original native circuit as the incumbent throughout. Only accept a KMB after full forward/reverse/phase/scratch and physical FeMoCo verification. Neither a notebook score gain nor a passing new KMB was obtained this round.

Upstream inspiration and attribution: Griffith, Apache-2.0 (https://github.com/tsukushi-gate/Griffith). No Griffith implementation copied.
