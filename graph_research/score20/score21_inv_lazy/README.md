# invsqrt measurement-dependent product evaluation

The starting circuit is the score19 member with SHA-256
`684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`.
The final circuit is `staged_best.kmb` with SHA-256
`4b905da1d96c805946aa79f9214a490a616b182dd8b6890956f1bf55fd857d53`.

## Arithmetic change

Experimentally, two unconditional CCXs at canonical KMX indices 22310 and
22351 had no lasting data effect after their target registers were measured.
Deleting either left one cubic phase correction. One factor was a parity of
several live wires. The compiler computes that parity with CX gates, applies
a CCZ under the existing HMR result, then reverses the parity circuit.

The two changes overlap in a single correction block. The combined version
computes the first product only inside that active block. The second product
then contributes through a factored CCZ on the correctly restored first
product. The first product's added HMR phase is paid with a conditional CZ.
Other correction blocks use Clifford terms recovered from the original
circuit's reachable input states. Both charged operations now execute
with probability one half, for an exact saving of one Toffoli-like operation
per shot. A separate restricted-window interpreter compared data state,
sign phase, and outgoing original classical bits on all 3,133,452 inputs
and all 64 assignments of the affected HMR outcomes.

The same region has six other temporary products with contingent read-only
uses. Each is computed just before its first active request, then held
until the original HMR. The classical guard versions refer to independent
existing HMRs. If no request was active, the HMR acts on zero and a conditional
CZ restores the original sign from the two product controls. For each
temporary the controls' product was compared against the original product on
all 3,133,452 inputs at every possible materialization point and at erasure.
No other non-phase operation writes the temporary before its erasure. A later
nested request is covered whenever an earlier active broader request already
materialized the value.

| Product target | Independent requests | Exact mean Toffoli saving |
| --- | ---: | ---: |
| q31 | 2 | 1/4 |
| q28 | 3 | 1/8 |
| q35 | 4 | 1/16 |
| q33 | 4 | 1/16 |
| q29 | 5 | 1/32 |
| q9 | 6 | 1/64 |
| Two overlapping corrections | One common guard | 1 |
| **Total** | | **99/64 = 1.546875** |

## Verification

The original official verifier passed the final KMB at its default
64 shots per input, **200,540,928 shots** across all legal inputs.
Its measured cost was **78,602.3170459352** compared with
**78,673.55534364567** for the pinned baseline. Replacing only this member
in the score19 portfolio raises the local score from 27.32812350537394 to
**27.336376956535187**. The maximum error-to-tolerance ratio was
**0.9986660009092673** at x=159, with the original 46 qubits, 33 generic
rotations, and rotation epsilon **6.003064377662461e−13**. Its static
Toffoli-like count is 1,568 because alternative guarded placements count as
separate instructions. The official cost uses the mean operations actually
executed. Its reaction depth is 1,346, compared with 1,336 in the baseline.

An independent exact evaluation of the full classical control decision
diagram found mean Toffoli counts of 1,478.75 and 1,477.203125 for the
baseline and candidate. This confirms a cost reduction of 71.15625 units
at 46 qubits. See `exact_count.py` and `exact_count.json`. The official sampled means are in `staged_best_official_one.json`
and `staged_best_official_full.json`. The one-shot pass independently
covered all 3,133,452 inputs and measured cost 78,602.49831867768.

The ordinary official verifier SHA-256 is
`ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`.
No Kaggle submission was made.

## Reproduce

From the repository workspace, using Python with NumPy and Kickmix:

```sh
p=score21_inv_lazy
base=invsqrt_new/rebuilt_source.kmb
python "$p/weighted_cones.py" --source "$base" --target 22310 22351 --out "$p/dense.json"
python "$p/combine.py" --source "$base" --dense "$p/dense.json" --out "$p/combined.json"
python "$p/staged_clauses.py" --source "$p/combined.kmb" --out "$p/staged_best.json"
python "$p/exact_count.py" --baseline "$base" --candidate "$p/staged_best.kmb" --out "$p/exact_count.json"
python "$OFFICIAL_VERIFIER" "$p/staged_best.kmb" --max-workers 4
```

The last command uses the regular 64 shots per input. For the full-domain
one-shot check, add `--shots-per-x 1 --batch-size 292`.
`lazy.py` imports the earlier packed trace and scope parsing utility
`highest_graph/phase_cone/rewrite.py`.
