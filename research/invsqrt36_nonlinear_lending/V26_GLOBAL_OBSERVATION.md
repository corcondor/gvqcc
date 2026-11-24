# V26: global observation quotient and deferred nonlinear carriers
Research only. NOT SUBMISSION. Do not merge into main. All counts are native KMB diagnostics; maximum width remains 37Q and no official score update. Source V25 archives and PR68–72 compared; exact NAND counterexample from PR72 excluded. Four older ANGLE archives remain unrecovered. No world-first claim.

## Verified portfolios (exact legal domain)
- V25 low parent SHA 0e2951f0516ab0c3f02e5ee29df4e436c696a6253bf54994fb142bd46a33ba89: 58208 ops/E=22501/16.
- Global observation: 13622 diagonal observations/1370 sampled guard classes; 2121 candidate zero relations, 1245 exact pass, 1164 disjoint chosen, 1422 commands deleted, zero paid savings. Parent after phase pass cc7fa77be361158505dcd50b7cb641a99eba613d1e8b17791653182d850d38bb.
- Low deferred: 764 proposals/707 exact pass, 87 selected. Independent serialized mapped replay PASS, 3133452 legal inputs, 1276 symbolic HMR variables. 56734 ops/E=22501/16/static1551, 8189→7519 full-occupancy cut count against phase-only parent; 829 source full-occupancy cuts virtualized in 36Q bodies, 770 mapped body commands, one closed chart (18 source full cuts). SHA 8db1710226832911e0499238017e4f572033ec37ccd8546d7183587b092abb97.
- V25 joined parent SHA 4cca0e26e36d48939c50815ea0cb8a13e9c042e63adf302f6e1ad41bf9ba9809: 53155 ops/E=22725/16. Global observation: 12053 phase observations, 857 proposals, 33 exact pass, 24 disjoint selected, 95 removed. Phase-only SHA 75cef2f6dd38ae211943e086fe86dc4d97864392036c4ae619bc2e455ad7205a.
- Joined deferred: 808 proposals, 751 exact pass, 72 selected. 53049 ops/E=22725/16/static1565, 6388→5765 full-occupancy cuts against phase-only parent; 757 source full cuts virtualized in 36Q bodies, 764 mapped body commands, one closed chart (18 source full cuts). SHA a5aed434fc6308a0b4824ef970952e87512f5ac1aaa214f06ba8d1013d7daef8. Independent serialized mapped replay PASS over 3133452 legal x, 1289 independent HMR symbols; state, classical, phase, rotations, guard and exact costs.
- Nonlinear data read extension: 256 sample successful read replacements, 1520 endpoint proposals, 1024 retained, 841 exact pass. Selected same final SHA and cost/pressure; no extra gain. The naive nonlinear update deletion/deferred phase debt screen (1526 starts, 482389 steps) did not yield a valid paid reduction; all 38 joint repair candidates fail full-domain data equality. Do not count rejected candidates.
- Pure phase removal does not reduce width; actual chart body physical mappings distinguish source cuts from changed instruction counts. Partial charts do not imply a globally connected 36Q circuit.

## Mathematical connection
Pull back diagonal observations to common input/history coordinates. Any zero XOR relation can be deleted without changing data, HMR, rotation controls, or classical control flow. A guarded triple from actual joined source positions (15191,15206,15231) and four parallel triples: m*a*b + m*a*u + m*a*(b+u)=0 over GF(2), with real CX(32,30) at 15203, intervening HMR and rotations preserved. Separately, a virtual carrier with t=a*b+a+c can replace Z(t) by Z(a) Z(c) CZ(a,b), delay all writes, and reconstruct only at the last data read. Actual [34345,34416) uses q8, q5, q20, q22. Lean covers universal algebra and these concrete projected identities; full-domain reachable premises and serialized KMB proof are checked separately in Python, not fully formalized in Lean.

## Score, frozen PR43 model
S=33.17031640530013*(60927.54794503887/(Q*(E+240.37798500105055)))^(1/3).
E=1406.3125: 37Q 33.17031641; hypothetical36Q 33.47464823, additional E strictly less than 45.74140236.
E=1420.3125: 37Q 33.07684213; hypothetical36Q 33.38031635, budget <31.74140236. These are predictions, not official scores.

## Reproduce
The companion conversation ZIP contains original V25 KMB bytes, native parser/BDD engine, all candidate generators and receipts, and mapped fragment gate lists. Run in v25 directory:
```
python v26_phase_global.py low_guard_NOT_SUBMISSION.kmb v26_low_phase.kmb
python v26_phase_global.py joined_guard_NOT_SUBMISSION.kmb v26_joined_phase.kmb
python v26_defer.py v26_low_phase.kmb v26_low_defer.kmb
python v26_defer.py v26_joined_phase.kmb v26_joined_defer.kmb
python v26_finalize.py v26_low_phase.kmb v26_low_defer.kmb v26_low_defer.json
python v26_finalize.py v26_joined_phase.kmb v26_joined_defer.kmb v26_joined_defer.json
```

## Additional literature and relevance
- Yang & Yuan, MBUndo: Sound, Automatic, and Efficient Measurement-Based Uncomputation for Quantum Circuits (preprint 2026-11-02), https://arxiv.org/abs/2611.02345 : sound measurement locations and generalized phase corrections. Especially relevant to the currently failing joint data/phase debt search.
- Paradis, Bichsel, Vechev, Reqomp (Quantum 2024), https://doi.org/10.22331/q-2024-02-19-1258 : bounded-space uncomputation planning.
- Paradis et al., Unqomp (PLDI 2021), https://doi.org/10.1145/3453483.3454040 : dependency-based uncomputation.
- Hietala et al., A Verified Optimizer for Quantum Circuits (POPL 2021), https://doi.org/10.1145/3434318 : verified semantics-driven compilation.
- Amy, Roetteler, Svore, Verified compilation of space-efficient reversible circuits (CAV 2017), https://www.microsoft.com/en-us/research/publication/verified-compilation-of-space-efficient-reversible-circuits/ : verified cleanup and space usage.
- Khattar & Gidney, Rise of conditionally clean ancillae (Quantum 2025), https://doi.org/10.22331/q-2025-05-21-1752 : conditionally available workspace, relevant to closing chart boundaries.
- Ruiz et al., Quantum circuit optimization with AlphaTensor (Nature Machine Intelligence 2025), https://doi.org/10.1038/s42256-025-01001-1 : structured gadget/tensor search, not directly implemented here.
- Martiel & Goubault de Brugière, Architecture aware compilation of quantum circuits via lazy synthesis, https://arxiv.org/abs/2012.09663 : deferred frame materialization (related principle, different objective).
- Amy & Lunderville, Linear and Non-linear Relational Analyses for Quantum Program Optimization (POPL 2025), https://doi.org/10.1145/3704873 : phase folding with classical guards and nonlinear relation analysis (retained prior reference).
