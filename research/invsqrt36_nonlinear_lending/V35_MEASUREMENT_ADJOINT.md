# V35 — measurement adjoint and moving packed coordinate
Research only, NOT SUBMISSION. Based on PR85, also independently replayed PR84 budget. No main merge or Kaggle submission. Full width remains 37Q.

## Exact serialized portfolios
|parent|ops before/after|full occupancy before/after|E before/after|independent HMR|
|---|---|---|---|---|
|PR84 budget|54311/54314|4576/4177|23221/16 unchanged|1299|
|PR85 physical slots|51019/51024|3809/3702|23077/16 unchanged|1281|
|PR85 low scheduled|55986/55989|4869/4759|22501/16 unchanged|1276|
|V35 slots + XOR pair|51024/51030|3702/3681|23077/16 -> 23221/16|1281|

All legal inputs (3133452) and independent HMR variables, per-source-step comparison of serialized KMB data, phase, rotation observations, scopes, and classical record semantics. PR85 report 3818 cuts was pre-slot; re-read final slots file gives 3809. Full oracle is 37Q. No direct savings of PR71's 80 pairs or improvement over E1406.3125.

SHA256:
- budget parent dab4064cf176e96db2c75d28fddb2f28336ff7125a43f99f91a460fe197d89b1 -> eaf13b525084e1baa73e9b84d5e3b6d84a7eb041be5b5b46762aec1844b9bbcf
- slots parent 8039c8a9c33adaebb61c162b3057368431c8bfaa3418eecbec9f60d511c811e9 -> d873f84acb4a9afb5652f7f56597728953beb60d91afdb7262a6a4249e9f8274
- low parent d734fe6ea3544bc1096e08d36dda5ff862f647feb1917f3daad1cdc0ad3ae539 -> 01a500fa6f638798c6b3fb3dfcf45b8308c1abd8a0b522fb0aafd867c1650824
- pair addition 75a98a62d4f09b5a8120ed952b4ff291cbff8e99ab345e4d4eb244a78d04ea0e

## Implementations and negative results
Advance HMR with paired outcome m; projected omitted wire zero, writes q ^= f become phase m*f; guarded writes preserved and reads synthesized in remaining coordinates. Local exact phase-debt invariant m*(q_before XOR q_after), and fresh serialized verification. Budget: 185 sampled proposals,182 exact accepted,167 disjoint, 399 relief; 166 direct original records,1 snapshot. 150 are pure retiming,17 have changed operations (145 relief). Slots: 45/41/22, 107 relief; low:46/43/21,110 relief. Dense degree-two and signed literal-times-affine fit: 113/109 proposals on slots, same selected SHA at zero budget. Earlier full virtual lifetime screen 390 windows,3 proposals,1 exact accepted (+1 E/18 relief), not selected. 

Moving packed pair XOR frame: project q XOR r to r, q=0, update packed coordinate directly, synthesize actual source reads, preserve HMR sign using survivors; 259 runs,9324 pair candidates,64878 steps,132 sample passes,5 selected for exact checks,3 accepted,2 rejected. At zero budget unchanged. Positive budget 3 disjoint eight-op motifs [17026,17034),[17145,17153),[17314,17322) each +3 E and 7 fewer full cuts; independent serialized replay PASS. Not a globally linked 36Q solution.

## Carry exchange obstruction
Observed 161 consecutive CCX(a,b,d), CX(c,d), CX(c,a), HMR(c) windows with d=0 at entry on sample. Endpoint u=a XOR c, v=ab XOR c=ub XOR c*(1 XOR b). For each of 2048 sampled actual legal inputs/measurement histories, fit bc against all degree<=2 monomials of common coordinates (u,b, other unchanged coordinates). 161/161 inconsistent (augmented rank one larger). 138 have input/output affine ranks 37 each, common 36, union 38; 22 have 35/35/34/36 and 1 34/34/33/35. This excludes the specified common-coordinate quadratic decoder on those actual rows, not all nonlinear compression. For 138 full-rank cases, an affine--one-CCX--affine data-only rewrite on 36 wires with these boundary functions is also excluded: shared span is the intersection, two controls must lie in it, and endpoint change ab would have to belong to its degree-two span. Does not exclude measurement-adaptive, joint multi-motif, different-boundary or higher-degree synthesis. No Lean proof of reachability or general rank obstruction.

## Literature
Rovara/Burgholzer/Wille arXiv:2511.22712 dynamic measurement retiming; Yang/Yuan arXiv:2611.02345 MBU soundness and phase correction; Amy/Lunderville arXiv:2410.23493 relational phase folding; Shah/Fiszer/Perkowski arXiv:2608.27430 containment and complemented affine factor screen (no new zero-cost fit); Venev/Gehr/Dimitrov/Vechev arXiv:2406.14227 modular uncomputation/adjoint (inspiration for lifetime IR; no direct Silq implementation import). Lean 4.35.0 certificate for Boolean identities and bookkeeping, distinct from Python exact verifier. Companion archive holds actual Python sources, native inputs, outputs, receipts and run commands. No claim of world-first novelty; old ANGLE source archive audit still incomplete.

Conditional PR43 score model only, no official verification. Fixed 36Q break-even E1452.0539 vs original baseline: zero-cost slots margin 9.7414 E, pair variant margin 0.7414 E. Prefer zero-cost joint boundaries rather than paying for each carry-exchange.