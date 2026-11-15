# invsqrt normalization-marker overlay

The pinned circuit is the score19 invsqrt member, SHA-256
`684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`.
At the normalizer's relevant reads, q25 indicates `1 <= x < 64`.
The two q25-controlled runs of 12 swaps are part of the phase evaluator's
normalization. Their adjacent q24-controlled matchings have two 13-vertex
paths in their union, so this matching analysis gives zero shared swaps.

## Executed circuit

An intermediate value can carry q25 as an XOR offset across a q25-idle
interval if the induced offset on each gate remains constant across the 63
active input rows. The patch XORs a marker into an existing data wire,
measures and resets q25, follows the resulting offset through the original
gates, and reconstructs q25 as a parity of the encoded endpoint. It then
restores every offset and pays the added HMR sign with a conditional Z on
the reconstructed q25.

Selected intervals leave all original phase predicates and HMR inputs
unchanged. Their q25 decoder is verified directly over every legal input
using packed Boolean evaluation. Above x=63 the injected offset is zero.
For all 63 active inputs the proof checks the offset propagation through
each classical branch and its return at the branch join. The only new
measurement sign is `(-1)^(m*q25)`, canceled by the emitted conditional Z.
The proof applies for either value of each fresh outcome.

| Metric | Verification |
| --- | ---: |
| Local all-nonzero regions bridged | 17 of 453 |
| Local peak cuts bridged | 68 of 3,742 |
| Overall qubits | 46 |
| Static Toffoli-like operations | 1,550 |
| Generic rotations | 33 |
| Measured reaction depth | 1,336 |
| Original / overlay operations | 23,881 / 24,001 |
| Worst phase error / tolerance and input | 0.9986660009092673 at x=159 |
| Rotation epsilon | 6.003064377662461e−13 |
| Unmodified official verifier, one shot for each x | PASS, 3,133,452 shots |

The overlay KMB SHA-256 is
`410a22006e92d6c6213a0acb75947e915a55aec70bf10a80470facb1d5aba5a2`.
Its one-shot mean Toffoli count is a sample statistic. The added instructions
are CX, HMR, and conditional Z. The original paid instructions retain their
execution laws. No structural score change is available, and this KMB is
an experiment.

## Full-span obstruction

The SAT update represents each wire offset as a Boolean variable, checks
every active local data pattern, enforces equal offsets at branch joins,
and requires each phase offset to be a constant on the active domain.
Requiring restoration of q25 using the full-domain affine endpoint
relations yielded UNSAT across each whole body interval. All 12 longest
individual peaks also returned UNSAT at their nearest lower-width endpoints.
Exact packed collisions also show that the scanned q22/q23/q24-only overlays at the
tested endpoints identify between 59 and 63 of the 63 small inputs with
a larger legal input. Such collisions rule out any decoder of those
encoded endpoint states.

## Alternate 25-bit input code

The integer-code fixture `normalized_code.py` keeps three bits of the
base-4 exponent, and a 22-bit normalized mantissa. For inputs 1 through
15 the low bit is set in an otherwise even mantissa lane. Inputs 16
through 63 use the unused mantissa lane starting at `3 * 2^20` in the
top exponent class. All other inputs retain their ordinary mantissas.
The decoder reconstructed both x and q25 on every legal input. This
is an arithmetic-interface option. It does not yet implement the
small-input phase evaluator using those changed mantissas.

## Alternate 25-bit input code

The integer-code fixture `normalized_code.py` keeps three bits of the
base-4 exponent, and a 22-bit normalized mantissa. For inputs 1 through
15 the low bit is set in an otherwise even mantissa lane. Inputs 16
through 63 use the unused mantissa lane starting at `3 * 2^20` in the
top exponent class. All other inputs retain their ordinary mantissas.
The decoder reconstructed both x and q25 on every legal input. This
is an arithmetic-interface option. It does not yet implement the
small-input phase evaluator using those changed mantissas.

## Reproduce

```sh
# Run from this directory, with an absolute path in PINNED_INVSQRT.
export PYTHONPATH="$GVQCC/graph_research/score19/experiments/phase_basis:$GVQCC/graph_research/invsqrt"
python emit_partial.py --source "$PINNED_INVSQRT" --peaks selected_peaks.json --out replay.json
python "$OFFICIAL_VERIFIER" replay.kmb --shots-per-x 1 --batch-size 292 --max-workers 4
python peak_probe.py --source "$PINNED_INVSQRT" --out peaks.json
python gauge_sat.py --source "$PINNED_INVSQRT" --out gauge_sat.json
python normalized_code.py --out normalized_code.json
python collisions.py --source "$PINNED_INVSQRT" --out collisions.json
```

The bounded check of the 12 largest individual peaks also returned UNSAT in
this affine overlay model. See [the check](large_peaks.py) and [its results](large_peaks.json).

The official verifier SHA-256 is
`ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`.
`gauge_sat.py` requires z3-solver in addition to the NumPy and Kickmix
dependencies of the other scripts. The experiment imports the earlier
packed Boolean trace tools from `highest_inv_next` and `graph_inv`.
