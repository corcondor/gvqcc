# Terminal controlled-swap measurement rewrite: bounded scan

## Result

No new circuit reduction was found by this pass. All 12,240 controlled swaps in the pinned DQI821 circuit and all 129 in the verified local inverse-square-root cache candidate were inspected. The forward search limit was 4,096 instructions per site. There were no strict matches and no affine terminal-readout candidates within that limit. No circuit or submission was modified.

A single requested follow-up extended **only the affine-cone pass** to 16,384 instructions, with a 240-second time budget. It completed all 12,240 DQI sites in 127.12 seconds and again found zero hits. Of the 2,560 previously capped sites, 1,116 now reached a concrete CCX dependency and 1,444 remained capped. No further extension was run.

| Circuit | SHA256 prefix | CSWAP sites inspected | Strict matches | Affine cone candidates |
|---|---|---:|---:|---:|
| DQI public baseline | `821bf8d157c0` | 12,240 / 12,240 | 0 | 0 |
| Local verified invsqrt cache candidate | `684106f10173` | 129 / 129 | 0 | 0 |
| Older local invsqrt file, auxiliary check only | `e0db1ac70e25` | 129 / 129 | 0 | 0 |

The newest public invsqrt `1ba197b0...` was not present locally and was not tested.

## Chosen pattern and why this was a new boundary

The source is pattern P16 in [Almond, Design Patterns for Optimizing Quantum Circuits, Dispatch 1](https://almond.org/writing/quantum-circuit-design-patterns-1), published 2026-11-11. A controlled swap followed by X-basis measurement/reset of both targets can be replaced with CNOT, two measurements, and a measurement-conditioned CZ. The classical records must also change: if the new records are `u,v`, the old records are `r=u XOR v, s=v`. Saving: one Toffoli, no extra quantum storage.

Previous pair and phase scans use measurements as boundaries. This pass expressly inspects a unitary-to-measurement boundary. It extends the direct adjacency pattern by allowing commuting unrelated gates and symmetric diagonal phases before the two measurements. A second, discovery-only pass propagates the controlled-swap difference through CNOTs and swaps to find affine terminal-readout cones.

For the strict rewrite, the control must not be overwritten before correction; both targets must reach measurement without disallowed intervening reads; the first measurement record must not be used before the second record is available for relabeling. Scope changes are barriers. An affine-cone hit alone would not authorize a rewrite: its classical records and phase still need a construction and proof.

## What blocked the DQI sites

| Affine-cone stopping reason | Sites |
|---|---:|
| Control overwritten | 5,340 |
| Affected value used by CCX | 2,564 |
| Reached the 4,096-instruction limit | 2,560 |
| Affected value used by another CSWAP | 1,092 |
| Scope/debug/unknown-operation barrier | 624 |
| Affected value used by conditional CZ | 60 |

The 2,560 capped sites remain unresolved beyond the tested window. Zero matches is not a proof that every possible measurement-aware CSWAP rewrite is exhausted.

After the 16,384-instruction follow-up, the CCX-barrier count is 3,680 and the capped count is 1,444; all other stopping counts are unchanged. Exact remaining capped positions are recorded in `outcome_pattern_terminal_cswap_dqi821_extended.json`. These 1,444 cases are not ruled out beyond that window.

All invsqrt sites stopped at an actual operation barrier before the limit: 105 control writes, 21 dependent controlled swaps, one scope barrier, one CCX and one conditional CZ.

## Verification and artifacts

The local signed-basis identity was checked on all 8 input assignments and all 4 measurement records: 32 cases. Eight matcher fixtures confirm accepted direct/nonadjacent patterns and rejection of control writes, premature record uses, phase dependence, and scope changes. The affine discovery pass deliberately does not certify record dependencies.

Files:

- `outcome_pattern_terminal_cswap_scan.py`: read-only scanner.
- `outcome_pattern_terminal_cswap_dqi821.json`: complete 12,240-site bounded scan, 62.67 seconds.
- `outcome_pattern_terminal_cswap_dqi821_extended.json`: affine-only 16,384-instruction extension, all 12,240 sites, 127.12 seconds.
- `outcome_pattern_terminal_cswap_invsqrt_cache.json`: verified local cache candidate scan.
- `outcome_pattern_terminal_cswap_invsqrt.json`: older local-file auxiliary scan.
- `outcome_pattern_terminal_cswap_fixture_checks.json`: exact identity and matcher checks.

No same-control CCX scan or 42-factor tensor search was repeated.
