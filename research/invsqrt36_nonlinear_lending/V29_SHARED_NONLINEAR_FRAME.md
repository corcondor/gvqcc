# V29 — shared nonlinear delta frame, measured atom reuse, quotient compression
Research only; NOT SUBMISSION. Parent V27 source SHA256 bd91d88909de18643262178477ca813c67dbcb2edc3325a99e66c964d6758258. V28 budget baseline E=1451.8125, 54148 commands, 45685 covered source commands, 5567 full-occupancy cuts. No main change, official score or global novelty claim.

## Actual implementation
- Joint deletion of up to three paid mapped-body operations; shared endpoint RREF over the quotient by unchanged output coordinates; guarded phase repair and existing phase-observation reuse. Exact serialized BDD verification, all 3133452 legal inputs / 1276 independent source HMR symbols.
- First 2557 trials across 44 V28 bridges, 17 exact improvements, 24.5 expected paid reduction in the candidate portfolio, not whole-oracle savings. Exact frame audit: 24 deleted data updates, 20 later equal-product occurrences, all 17 bridges have reuse, up to 8 affected coordinates but rank at most 2, four nonzero measurement phase debts. Sixteen bridges have one atom in the fixed dictionary, one has two. [31155,31169): 4→3 paid, 18 ops unchanged, repair early deleted product via conditional Z on later reconstructed product. [33774,33902): expected 11.5→5 after repeated deletion; [39191,39444) second-pass 83/8→79/8. [36030,36130) extra reuse 5/2→2 exact pass; other candidate rejected on phase.
- Direct original low-cost V27 source deletion and paired deletion screens no gain: 1276 starts, 3896685 steps, 339005 endpoint tests; 26368 paired windows. Do not repeat frozen screens or interpret sample fits as proofs.
- Persistent permutation frame and affine-word compression (quotient canonical form, exact affine-map checks), avoid per-chunk restore within connected 36Q groups.

## Verified serialized hybrid results
All retain maximum 37Q, exact comparison against V27 original for data, phase, HMR, classical, guard and rotations. Each has 3133452 legal inputs and 1276 independent HMR variables.
| variant | expected paid | static paid | native commands | covered source | groups | full cuts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V28 budget | 1451.8125 | 1606 | 54148 | 45685 | 305 | 5567 |
| V29 fixed lazy | 1443.8125 | 1597 | 54308 | 45685 | 305 | 5567 |
| V29 fixed compact | 1444.8125 | 1598 | 54109 | 45685 | 305 | 5567 |
| V29 budget compact | 1451.8125 | 1604 | 54072 | 45975 | 300 | 5281 |
| V29 budget lazy | 1451.8125 | 1604 | 54300 | 45997 | 300 | 5258 |
Hashes respectively for V29 fixed lazy / fixed compact / budget compact / budget lazy:
6ff22e18d1461ad0456ae348870980eafa43b639e28cdde3b246831e5655e900
e668599e8b053388fc85ba4c34f8c44718fdbf98d1183cc7cec9477c68e3dcb3
aad166e36f9cf59062329115d7593d824a9761b27011e025222fc59d11959ddd
41813e87b3525e3fa9246aa11c6b98bb545bf9daedc5b3098c72265ef832b076

## Mathematical connection and literature
- Bernasconi, Cimato, Ciriani, Molteni, Multiplicative Complexity of XOR Based Regular Functions, §2.3 and §3: https://air.unimi.it/retrieve/dfa8b9a9-e631-748b-e053-3a05fe0a3a96/main.pdf — affine equivalence and quotient restrictions; adapted as unchanged-coordinate quotient normal form, not full autosymmetry/D-reducibility algorithm.
- Yu et al., Back-end-aware Fault-tolerant Quantum Oracle Synthesis (ASP-DAC 2025), §§5–6: https://si2.epfl.ch/~demichel/publications/archive/2025/ASPDAC25_YU.pdf — context-dependent AND costs, adapted joint native cut synthesis and budgeted selection, not their SAT database algorithm.
- Amy & Lunderville https://doi.org/10.1145/3704873 — relational nonlinear phase analysis: BDD equality of reachable atoms and phase repairs, not original polynomial abstract interpreter.
- AlphaTensor Quantum https://doi.org/10.1038/s42256-025-01001-1 — grouping shared decomposable atoms and context cost, not the RL search or T-count tensor solver.
- XAG synthesis https://doi.org/10.1038/s41534-021-00514-y — shared multiplication logic; not full port.
- Weighted finite-field summation by parts and scalar adjoint recurrence formalized in Lean; actual implementation uses forward exact delta/phase transport, not yet general backward adjoint search. Lemmas also cover affine product symmetry and the projected native [31155,31169) suffix. Lean 4.35.0 CI PASS at 858ac805374d7c738f9f7003e00f41563feec796, https://github.com/corcondor/gvqcc/actions/runs/45487399808 . Not a complete Lean proof of native reachable state equivalence.
- Peer PR75 HMR quotient has a different native parent. No arithmetic addition of savings, no unvalidated merge. Four historical ANGLE source archives remain unavailable.

## Conditional model
Fixed lazy E1443.8125: 37Q 32.92227739, hypothetical36Q 33.22433350. Remaining extra expected cost <8.24140236 before frozen break-even E1452.05390236. Fixed compact: hypothetical36Q 33.21776037. No official gain and full 36Q still missing.

## Reproduction
Companion conversation ZIP includes engine, original V27 source, pinned V28 bridge/chart artifacts, V29 search/audit scripts, integration scripts, serialized candidates and receipts. From archive root, use Python:
```
python v29_bridge.py
python v29_bridge_sparse.py
python v29_bridge_quotient.py
python v29_bridge_second.py
python v29_atom_reuse.py
python v29_frame_audit.py
python v29_lazy_integrate.py fixed v29_fixed_lazy_NOT_SUBMISSION.kmb
python v29_compact_integrate.py fixed v29_fixed_compact_NOT_SUBMISSION.kmb
python v29_compact_integrate.py 731/16 v29_budget_compact_NOT_SUBMISSION.kmb
```
No official verifier invoked. 
