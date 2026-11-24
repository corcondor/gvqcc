# V36 moving omission and measurement debt
Research only, NOT SUBMISSION. Actual source and generator are packaged in GVQCC_V36_MovingDebt_NOT_SUBMISSION.zip in chat. This branch records certificates and experimental receipts; the archive contains complete Python engine, generator, native parents and both serialized output circuits.

## Pinned results
PR87 physical source: 320 windows, 14869 decoder queries, 9053709 product probes, 32063 exchange edges; 11/11 exact local passes, 198 full cuts, +12 E if all selected. No integrated claim for this track.
Peer V35 combined parent SHA256 4b7cfdd3d84ab8eff7494c45da3f583c7c476c571cc997e0fd3b9ca6d417abbc, same parent as PR88: 51321 operations, E22991/16, 3554 full cuts, 1281 HMR. Bounded 280 windows, 11697 decoder queries, 7166084 products, 31406 exchange edges, 20/20 exact local passes, 272 full cuts, +21 E if all selected. Earlier 360-window screen interrupted; 280 completed. No claim of exhaustive search.
- +15 budget: 15 disjoint bodies, 51380 ops, E23231/16=1451.9375, static1602, 3303 full cuts, 1290 independent HMR, 6 original outcomes pre-sampled, SHA c576de278ca598b1d0152f475e93861b7188d90793eba71a03592cf0e3c2e4ec.
- +9 economy: 9 disjoint bodies, 51360 ops, E23135/16=1445.9375, static1596, 3352 full cuts, 1288 independent HMR, 2 original outcomes pre-sampled, SHA 2b49b859134cce45873a8477f19349e02fffd8f5d9c9822282342f6d5474b394.
Both fresh serialized replay PASS all 3133452 legal inputs, clean prefix coin preparation, aligned original events, independent extra events, final scratch reset, data, phase, rotations, scope, guard and classical record equivalence. PR88 separate outcome quotient not merged. Postpass on 43 newly emitted paid operations: zero sparse affine-reset candidates. No paid-gate minimum improvement, no full36Q, no official score, no main/Kaggle change.

## Implementation
State (omitted coordinate, outstanding measurement debt). Direct exchange z=w XOR H(u) realizes z in the retained w slot, settles old phase debt and leaves w virtual. Virtual writes z XOR= h contribute conditional phase m*h when a ghost measurement m is outstanding. Original HMR can be pre-sampled on a clean prefix slot and stored in an unused classical record, then its sign synthesized in retained coordinates and record published at the original event. Original event identity is preserved; no postselection. Source [7877,7888) has actual two direct exchanges 36→21→36, source 11ops/2 paid, local candidate 13ops/3 paid (plus one prefix HMR), ten full cuts covered. Bounded beam retains paths per omitted coordinate and debt; cost may temporarily increase, not an exhaustive nonmonotone search. It does not yet carry multiple independent nonlinear omissions simultaneously. 
Lean 4.35.0 CI PASS run 45504998702 at 874387def102b701ef8c22ba0177db8c61a86c84: interval weighted phase identity, direct exchange, pre-sampled event branch sign, concrete projected source7877. This is not full Lean verification of KMB or quantum-channel semantics.

## Literature used and scope
Kornerup/Sadun/Soloveichik DOI 10.22331/q-2025-02-18-1636 (earlier reference): measured cleanup and delayed phase debt.
Venev et al. DOI 10.1145/3689785: delaying uncomputation and space overhead, adapted to state-dependent omission graph, not their Silq compiler.
Nam et al. DOI 10.1038/s41534-018-0072-4: affine phase representation and NOT transport; adapted virtual writes and phase corrections, not original continuous-angle optimizer.
Amy/Azimzadeh/Mosca arXiv:1712.01859: parity network objective; abstract/formulation, no full GraySynth port.
Wu/Deng ReOC arXiv:2608.07973: register isolation and eager/deferred cleanup, abstract only.
Amy/Lunderville DOI 10.1145/3704873: prior relational phase folding. No global novelty or paper algorithm reproduction claim.

## Reproduction
Run from archive v30 directory:
```
V36_SRC=v35_peer_combined_NOT_SUBMISSION.kmb python v36_moving_ghost.py screen 280
V36_SRC=v35_peer_combined_NOT_SUBMISSION.kmb python v36_moving_ghost.py verify
python v36_integrate.py v35_peer_combined_NOT_SUBMISSION.kmb v36_peer_verified.pkl 15 v36_reproduced_budget.kmb
python v36_integrate.py v35_peer_combined_NOT_SUBMISSION.kmb v36_peer_verified.pkl 9 v36_reproduced_economy.kmb
```
Saved candidates, receipts, and SHA manifest included. Frozen Q36 score estimate budget 33.17107690, economy 33.21037182; actual37Q estimated 32.86950497,32.90844264. No official score.