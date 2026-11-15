# invsqrt graph reconstruction screens

The baseline is the exact score18 member `684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`.
Its official local cost is 78,673.55534364567 at 46 qubits.
None of these bounded screens produced a candidate requiring the official verifier.

| Search | Observed |
| --- | --- |
| Constant wire factoring | 8,466 original snapshots still have 24 nonconstant scratch wires. |
| Affine basis compression | At 3,633 snapshots the 46 wire values plus the constant were independent on legal inputs. A single affine relation cannot remove a wire at those snapshots. |
| Charged gate replacement by supported-state Clifford action | One sampled CCZ candidate fails the full domain. No replacement accepted. |
| Route a product offset through the existing dataflow | 817,281 CCX pairs screened. Under an affine-remainder match 692 pairs passed the sampled product test and none passed the data and phase routing constraints. |
| One CCZ for a complete conditional correction | Ten scopes with 2–4 paid gates. No fit with a raw wire, a two-wire parity, and an arbitrary parity plus any quadratic Clifford phase. No fit from the block's structural affine control pairs. |
| Reuse products across classical execution branches | No exact repeated conditional-to-unconditional or equal-guard CCX products to seed cache construction. |
| Selector-conditioned CSWAP fan-out sharing | All 23 disjoint runs have full gate rank modulo their own selector. This includes both q25-controlled runs of 12 swaps on the 63 active inputs. |
| Controlled-linear rank scan from DQI | The existing C++ scanner checked 27 shared-selector windows up to 12 charged gates. No lower relative rank. |

The two q25 runs are restored data permutations with phase evaluation between them.
Removing one matching forward/reverse pair preserves the tested data register and scratch on all 63 selector-active inputs but fails the official phase interval for every tested pair.
The results describe the listed rewrite models and the pinned circuit.

Each Python script accepts the pinned KMB as its first argument and a JSON output path as its second argument.
The scripts that emit successful rewrites accept a candidate output path as their third argument.
Use `--affine-remainder --max-span 24000` to reproduce the extended product-direction run.
Give `phase_parity_block.py` the earlier repo checkout using `--prior-code` so it can reuse the already audited phase-block and HMR symbol extraction.
