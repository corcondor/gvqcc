# GF4096 inverse: existing 65-Toffoli block confirmed

The proposed 66→65 replacement does not produce a new saving at the identified current site: the 65-Toffoli cubic inverse is already present in both DQI821 and the qualified 9a82 candidate.

## Exact source and binary matching

The checked upstream source is the local Apache-2.0 Syed v12 distribution at `controller_work/work/round2/milestone152/source/`. Its `compact_inverse.py` imports `compact_inverse_twelve` from `cubic_inverse130.py`; the older routine is explicitly named `legacy_compact_inverse_twelve`.

Native KickMix builders generated all four complete templates, including cleanup measurements and conditional phase repairs. The scan matches entire opcode strings, every qubit operand, every measurement destination, and every classical condition under separate injective renamings of quantum and classical wires.

| Source template | Instructions | Static Toffoli | Total standalone qubits | DQI821 exact matches | DQI9a82 exact matches |
|---|---:|---:|---:|---:|---:|
| Legacy inverse | 1,495 | 66 | 36 | 0 | 0 |
| Cubic inverse | 1,993 | 65 | 36 | 1 | 1 |
| Legacy inverse plus coherent zero flag | 1,506 | 68 | 37 | 0 | 0 |
| Cubic inverse plus coherent zero flag | 1,998 | 66 | 37 | 0 | 0 |

The zero-match rows also have zero full opcode-string candidates, so these are not simply failed wire-renaming attempts. This is a statement about complete source templates; it does not exclude equivalent variants with modified instruction scheduling or surrounding allocations.

In DQI821, the exact cubic inverse occupies the half-open instruction interval `[30595392,30597385)`. Its input word is q12 through q23. It uses 24 existing temporary/output quantum wires, all within q864 through q888. It therefore already fits the global 889-qubit width. Output and internal wire orders are recorded in the JSON receipt.

## Cost conclusion

The two actual upstream native templates both require 24 extra qubits beyond their 12-bit source; the often-quoted 66T/18-extra-qubit independent reproduction is a different allocation implementation and is not interchangeable as a template. At the exact matched site, the current implementation is already 65T. New Toffoli saving identified: **0**. New circuit produced: **none**.

No replacement was attempted, so there is no new whole-circuit verification or new score claim. The standalone generated template files are research fixtures, not submissions.

Artifacts: `outcome_inverse65_template_scan.py`, `outcome_inverse65_template_dqi821.json`, `outcome_inverse65_template_dqi9a82.json`, and the four `outcome_inverse65_*.kmb`/`.kmx` fixtures. Each source hash and generated template hash is recorded in the receipts.
