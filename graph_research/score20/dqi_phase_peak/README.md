# DQI GF(4096) masked inverse phase at width 888

The accepted DQI input is the e4 binary, SHA256
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.
The patched experimental whole tape has SHA256
`9d97cda71833e8ae4776355b9c39d3b90fba6f778bf4e869345feff477892d1d`.

| Quantity | Accepted e4 | Masked inverse phase splice |
| --- | ---: | ---: |
| Whole-tape qubits | 889 | 889 |
| Static CCX, CCZ and CSWAP | 382,894 | 382,894 |
| Masked inverse phase work qubits at each site | 12 | 11 |
| Maximum branchwise width across the 82 replaced spans | 889 | 888 |
| Q889 positions in the 82 corresponding spans | 447,606 | 0 |
| Q889 positions outside those spans | 9,036,777 | 8,607,724 |
| Q889 positions in the whole tape | 9,484,383 | 8,607,724 |

The full binary passed the unchanged DQI verifier with 1,024 shots and zero
value or phase errors. The smoke settings used seed 7, batch size 256, one
worker and log2 delta −12. This result supplies no default-shot score.
The whole binary still has 889 qubits.

## Rewrite and boundaries

- The fixed phase's two final GF(16) ANDs each affect only the output phase.
  Replace their contribution by a CCZ on their two factor parities and a
  parity of the original output controls. The first three leaf ANDs keep
  their existing HMR corrections. Both variants execute exactly 27 paid
  gates for each nonzero input mask.
- Replace both quantum-workspace scalar multiplications around the fixed
  phase with in-place conditional elementary row operations. The inverse
  scalar's multiplication matrix is constructed and reduced entirely in
  classical bits. Reversible quantum row operations therefore apply the
  forward scalar to the source and its inverse restores the source.
- Bind 82 complete old masked wrappers with exact opcodes and injective
  physical operand renaming. The conservative lifetime audit finds every
  old work qubit zero on entry. The old and new functions preserve the
  source and the caller's mask, and restore all work qubits. The selected
  new work bank omits one old physical wire at each site.
- Initialize 412 new classical slots at every entry. Replacement reads of
  the original mask are preserved. For every removed classical write,
  prove that each subsequent surviving read receives an intervening
  unchanged overwrite on its enclosing condition scope or an ancestor.
  The proof treats a surviving read before such an overwrite as a failure.
  All 82 sites pass. Both opcode and operand bytes in untouched spans are
  copied from the original binary.
- Recount the actual new binary. An additional 429,053 original Q889 cuts
  in untouched spans retire because the old work bank is no longer left
  conservatively live across those boundaries. No new Q889 positions occur
  in aligned untouched spans. The 18 fixed-phase occurrences outside these
  82 wrappers contribute zero original Q889 positions.

## Reproduction

Generate the fixed and masked old and new fixtures with `dqi_phase11.py`
and its documented sources. Run `bind_phase_peaks.py` with the e4 binary,
its profile and the fixture directory. Run the existing branch-sensitive
lifetime executable on e4, then run `splice_phase_peaks.py` with e4,
the bindings, the old lifetime TSV and the fixtures. Run the same
lifetime executable on the new binary and pass both lifetime files and the
splice receipt to `compare_coverage.py`.

`splice_all.json` records each old and new range. `coverage.json` gives
retired cut ranges outside replacements in original e4 coordinates.
`stock_smoke.json` is the verifier's unchanged output.
