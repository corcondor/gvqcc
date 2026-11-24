# V27: measurement quotient and low-cost lazy frame
Research only / NOT SUBMISSION. PR73 low parent exact SHA256 8db1710226832911e0499238017e4f572033ec37ccd8546d7183587b092abb97. No main or Kaggle changes. Full 36Q and paid reduction not achieved. No global novelty claim. Historical ANGLE source audit remains incomplete.

## Implemented results
- Exact lazy permutation frame: 56,734 -> 53,416 commands; 3,339 unconditional out-of-scope SWAPs virtualized, 21 terminal swaps restore input ABI. E=22501/16 (1406.3125), static1551 unchanged. 7519->6733 all-nonzero cut count, not an equal number of new 36Q intervals. All 3,133,452 legal inputs, 1276 independent original HMR events; every original op compared with mapped data, branch phase, classical state, guard and rotation control. SHA256 bd91d88909de18643262178477ca813c67dbcb2edc3325a99e66c964d6758258.
- Transfer of previous affine-chart compiler to the new cheap parent: 143520 candidate relation checks, 104677 exact passes, 46794 cuts with certified affine relation (including 111 of 6733 all-nonzero cuts). This is a detected-relation count, not a proof of full rank at all other cuts. 321/321 segments independent BDD PASS (26799 relation checks), 44511/53416 source ops (83.328965%), longest [44696,53416) 8720 source ops. Hybrid 54064 ops, static1551, E=22501/16, peak37Q. Fresh serialized terminal/cost replay PASS, SHA 0d3ed15d892ddbb9fe0fa5a40e4cf2a68c90eb3115d7a30fbf701ea2082d9c96. Prefix and longest 36Q standalone segments are partial circuits only, not submitted or full oracles.
- Exact MBUndo-style interval lifetime scan on low parent: 0 intervals containing paid XOR writes ending at zero; extension to retiming existing unguarded HMR events with preserved outcome version also 0. 1171 nonzero-to-zero HMR events, 901 SWAP-coordinate zero transitions, 19 CX, 6 X (not all independent lifetimes). Full replay unchanged. Fixed-pivot moving-direction screen: 1082/1095 unguarded HMR endpoints, 8747/9279 backward steps, 1111/1138 direction changes, no eligible paid candidate (low/joined).
- New generated phase-observation pair search: 7,056,192 probes, 321 proposals, all exact rejected. BDD-guided witness coverage (not an iterative complete CEGIS solver): 4465 input/history samples, 13,755,456 probes, 21 proposals, all exact rejected. Captured source activation guard with new conditional Z/CZ observations: 9,608,896 probes, no candidates. Joint guard-group screen found no equal sampled activation guards across distinct paid source phases; sharing BDD root variable is not guard equality. Do not repeat random-only screens or count rejected edits.
- Mathematical connection: s=d XOR fv with d_p=0,v_p=1. CX(p,j) can update the virtual direction v XOR e_j without changing d. A sequence of target-XOR writes f'=f XOR parity(h) produces branch phase m f XOR parity(m h)=m f'. This extends the interval HMR rule to a moving affine quotient; fixed-pivot restriction had no positive paid native splice. Lean 4.35.0 proves guarded parity, interval MBU, moving coordinate identities, generic frame writes and resource arithmetic; CI PASS at 62c264fe3d3c9db2ea4476f3a4d9db69fcae2a6c, run https://github.com/corcondor/gvqcc/actions/runs/45481963953. Whole reachable-domain proof is BDD not Lean.

## Literature use audit
- Yang & Yuan, MBUndo (2026), https://arxiv.org/html/2611.02345v1 , §2.3 and §4.2 Algorithm 4: inspected actual interval rule (last use, X-basis measurement, in-place guarded phase corrections), implemented specialized scan, not a claimed reproduction of their benchmarks.
- Amy & Lunderville (POPL 2025), https://doi.org/10.1145/3704873 , §4 affine and §5 nonlinear relation framework: adapted principle of pulling phase observations back to reachable input/history functions; exact BDD, not their Gröbner implementation.
- Khattar & Gidney (Quantum 2025), https://arxiv.org/html/2407.17966v2 , §3 conditionally clean workspace and §4 toggle detection inspected. Motivates future conditional basis moves; no implemented paid gain attributed to this work.
- Martiel & Goubault de Brugière (Quantum 2022), https://doi.org/10.22331/q-2022-06-07-729 , lazy representation principle adapted to permutation frame, not their architecture routing algorithm.
- Reqomp (Quantum 2024), https://doi.org/10.22331/q-2024-02-19-1258 ; abstract and design objective consulted; full algorithm not ported.
- Additional related sources (not implemented or fully read): Quist & Laarman, general-circuit spooky pebbling, https://doi.org/10.46298/lmcs-21(4:29)2025 ; Kornerup et al., https://doi.org/10.22331/q-2025-02-18-1636 ; Patel/Markov/Hayes, https://arxiv.org/abs/quant-ph/0302002 ; Webster et al., A* and greedy CNOT/Clifford synthesis, https://doi.org/10.22331/q-2026-09-21-2212 ; Meuli et al., XAG compilation, https://doi.org/10.1038/s41534-021-00514-y ; Amy & Mosca, Reed-Muller phase decoding, https://arxiv.org/abs/1601.07363.

## Frozen model
Current actual37Q: 33.1703164053 (unchanged conditional model); hypothetical 36Q with unchanged E: 33.4746482342. Additional expected gate budget <45.74140236 at 36Q to exceed frozen benchmark. No official score or submission.

## Reproduction
Use companion conversation ZIP; engine dependencies are bundled. Run from v25 directory:
```
python v27_interval.py v26_low_defer.kmb v27_low_mbu.kmb
python v27_hmr.py v26_low_defer.kmb v27_low_hmr.kmb
python v27_moving.py v26_low_defer.kmb v27_moving_screen.json
python v27_lazy.py v26_low_defer.kmb v27_low_lazy.kmb
python v27_phase_mitm.py v26_low_defer.kmb v27_low_phase_mitm.kmb 128
python v27_cegis.py v26_low_defer.kmb v27_low_cegis.kmb 256
python v27_guard_transport.py v26_low_defer.kmb v27_low_guard_transport.kmb v27_low_cegis.witness.json 512
python v27_group_guard.py v26_low_defer.kmb v27_low_group_guard.kmb v27_low_cegis.witness.json
python v27_chart.py v27_low_lazy.kmb v27_chart_out
python v27_terminal.py v27_chart_out/chart_hybrid37_NOT_OFFICIAL.kmb
```
