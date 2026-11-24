# V6 guarded atlas and shared lifetime — diagnostic, NOT SUBMISSION

Stacked on PR #31 (V5 adaptive atlas), commit e63fce27433c57d461de6f20015146c13bb97358. Main and prior PRs unchanged. Source SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03.

## Real circuit results
- V5 wide: 53195 / 60766 source ops in 36Q charts, static/expected 1879/1705.3125, SHA d7e14b3cc42cebd9fc8df5047fc9f21978981f80841b34b5ea980c4f8fe4989d.
- V6 cost-first: two PR32 disjoint lifetime donors exactly matched and transplanted into V5 wide. Static/expected 1877/1703.3125, 62638 paired exact checks across 3133452 inputs and 1168 independent potential HMRs. SHA 6a560bac6573861684561dd666360d19d12b549356760470edfe844e274555f3. Coverage 53195 unchanged.
- V6 guarded atlas: 131 residual gaps, 33 complete IF regions, 28 flat IF screened. Branch-conditioned sampled affine/quadratic relation history, forward/backward substitution, dynamic latent omitted coordinates, branch-local chart switches, exact join to entry ABI. 1718 cuts, 334 nonlinear sampling cuts, 780 sampled nonlinear relation proposals. 18 candidate flat IF macros, 18 exact BDD accepted. Two additional unguarded proposals rejected. 1101 new source ops, 54296/60766 (89.35259849%), 6470 remain, 113 residual gaps. Whole source-to-hybrid 42726 exact composition checks PASS. Static/expected 1897/1714.3125; SHA ccfb6ecab9b384573950b33f621dd3b34e076ee2e004a80d4d82b5cf8319a142.
- V6 integrated: same 54296 coverage with both PR32 lifetime donors reapplied to the exact matching native ranges. Static/expected 1895/1712.3125, 62703 paired checks PASS across 3133452 inputs and 1168 potential HMRs; SHA 6c019efe46799071d79cc2930274a9b0ff09bd9603fcf1d2f74314fdfc04f1be. Neither native score nor full 36Q achieved; all variants remain 37Q diagnostics.
- Local arbitrary-boundary checks (entry omitted wire zero, both branch arms and arbitrary potential HMR/classical inputs): 12/18 pass; 6 require reachable-state assumptions; all 18 pass exact source reachability comparator. Do not promote the six to universal identities.

Exact accepted flat IF intervals (end exclusive): [21910,21956), [21982,22071), [22483,22532), [22561,22619), [23006,23053), [23084,23138), [23529,23581), [23615,23685), [24180,24250), [24642,24693), [25175,25230), [25280,25352), [25804,25875), [26867,26941), [28313,28359), [28404,28481), [28760,28806), [28845,28919).
Each adds one static CCX, expected 0.5 under the paired reference model. Cost-first and width-first are different diagnostic candidates. No official score gain; public 37Q expected paid 1406.3125.

## Lean
GuardedAtlasV6.lean: generic guarded join, measured-phase cancellation, latent write identity, actual native gate-list identities [21910,21956), [22561,22619), [25804,25875) with entry zero omitted wire and both branch arms, arbitrary HMR and phase. Resource theorems use literal gate lists. CI PASS at proof commit cef2a4b97960828c86cef4184452c556d06492d0: https://github.com/corcondor/gvqcc/actions/runs/45355175318 (all eight PR workflow runs succeeded at that commit). No full quantum-channel theorem.

## Reproduction
Use V6 archive (contains V5 bundle dependencies, source KMB, emitted KMB, exact receipts, scripts and logs). Only load trusted pickle files. Run inside central/global_chart:
```
python v6_atlas.py
python v6_guarded.py
python v6_verify.py
python verify_portfolio.py v6wide
python v6_combine_donors.py
python v6_integrate.py
python v6_check_coverage.py
```
Donor script derived from PR #32 shared-lifetime implementation, with parent file, receipt and output names changed. The bundle retains exact input and receipts; no official verifier or Kaggle submission.

## Additional literature and source links
Retain all V4/V5 references including DeepMind https://arxiv.org/abs/2611.09822 and https://github.com/google-deepmind/formal-quantum-computation, QAOA https://arxiv.org/abs/2503.09356, Amy and Lunderville https://doi.org/10.1145/3704873, MBUndo https://arxiv.org/abs/2611.02345.
- Amy, Towards Large-scale Functional Verification of Universal Quantum Circuits (2018), https://arxiv.org/abs/1805.06908 ; https://github.com/meamy/feynman — exact symbolic phase semantics.
- Amy, Roetteler, Svore, Verified compilation of space-efficient reversible circuits (2017), https://arxiv.org/abs/1603.01635 ; https://github.com/msr-quarc/ReVerC — verified register recycling and clean ancillas.
- Paradis et al., Unqomp, https://doi.org/10.1145/3453483.3454040 — dependency-aware uncomputation; also noted in PR32.
- Roetteler, Svore, Reversible Circuit Compilation with Space Constraints (2015), https://www.microsoft.com/en-us/research/publication/reversible-circuit-compilation-with-space-constraints/ — in-place operations and early cleanup.
- Xu et al., Quartz (2022), https://doi.org/10.1145/3519939.3523433 ; https://github.com/quantum-compiler/quartz — verified rewrite search.
- Yang et al., Quasar (2026), https://doi.org/10.1145/3808254 — equality saturation of multiple graph representations.
- Halpenny, Sireesh, Wallden, Fast, in-place, and ancilla-free quantum algorithms for integer multiplication and inversion (2026-11-19), https://arxiv.org/abs/2611.26605 — possible arithmetic redesign, not yet implemented.
External methods motivate operators; no external benchmark results are claimed as GVQCC gains, no external source code copied or forked. PR32's donors are verified actual code/data from this repository, not new discoveries. 

## Cross-session coordination
PR #32 provided the two reusable lifetime donors; PR #33's joint hub has a native 36Q implementation but no additive paid reduction on the corresponding closed carry chart. PR #34 provides complementary arithmetic/clean-borrow and amortized context bridge patterns. Do not sum their separate claims; require exact native interval matching and end-to-end BDD admission. The remaining 113 gaps (6470 source ops) are the next integration target.
