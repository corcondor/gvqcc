# Legacy GF24 guard removal: already absent in the current candidate

## Result

The proposed guard removal does **not** produce another reduction. The current
DQI binary already contains the unguarded implementation. This audit generated
no new candidate, changed no quantum or classical instructions, and ran no
additional official verifier.

Audited input:

- `/workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/dqi.kmb`
- SHA-256: `6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02`
- Q = 889, classical bits = 208167.

## Source and actual binary evidence

The old `night_c27/arithmetic/gf24_arithmetic.py` documents a guarded 483-T
product pair and an unguarded 462-T pair. Both admit a unit source, or jointly
zero source and original target. The extra guard shifts a zero norm to one,
inverts it, restores it, and erases its zero flag with a measurement correction.

The production provider is the later
`after_c5/arithmetic_t/gf24_nested_norm.py`, selected by
`after_c5/integration_v3/integrated_pipeline.configure`. Its nested inverse
saves three T gates in either variant. Thus the relevant production comparison
is **480 vs 459 T per pair**, or 381 vs 360 T for the closing alone. Both
unguarded providers require 24 helpers; the guarded providers require 25.

All production synthesis call sites found in the supplied source explicitly
pass `guarded=False`:

- `night_c27/synthesis/fixed_pipeline.py`
- `after_c5/integration/integrated_pipeline.py`
- `after_c5/integration_v2/integrated_pipeline.py`
- `after_c5/integration_v3/integrated_pipeline.py`

The only source call enabling the guarded component is the isolated
`check_arithmetic.py` check for `component == 'guarded483'`. The v7 runtime
overrides closed inverses and other providers but leaves the consuming-product
guard API unchanged. The older `fused_crt_synthesis.py` module docstring that
says joint zero requires `guarded=True` is stale relative to these explicit
production callers and the later inverse-zero extension.

The read-only matcher generated both providers' complete closing templates
and a short guarded-only `toggle_zero(norm12, flag); CX(flag, norm[0])` template.
It streamed the candidate SHA-256, checked its bound profile, scanned the entire
opcode column, and then required every quantum operand, HMR output, classical
target, condition, and angle to match under injective wire and bit renaming.

| Template | Closing T | Helpers | Opcode hits | Exact matches |
|---|---:|---:|---:|---:|
| Original guarded closing | 384 | 25 | 0 | 0 |
| Original unguarded closing | 363 | 24 | 0 | 0 |
| Production nested guarded closing | 381 | 25 | 0 | 0 |
| Production nested unguarded closing | 360 | 24 | 50 | 50 |
| Guard-only zero/shift motif | 11 | 10 temporary plus the flag | 18 | 0 |

Each of the 50 positive matches covers a complete **42,290-instruction**
closing. There are 16 such matches before position 36,505,264 and 34 more from
position 41,001,217 onward. Exact half-open ranges and hashes of their complete
wire/bit maps are in `score5_dqi_guard_scan.json`. This positive control ties the
conclusion to the actual production provider rather than only to a missing
source pattern.

## Phase, ownership, and limits

The 50 complete matches include every measurement and subsequent use of its
classical bit. They establish that the existing return blocks use the unguarded
provider's mask and phase operations exactly, up to consistent injective
renaming. Since no replacement is needed, no HMR mask is deleted, reassigned, or
left unpaid. No new coherent-equivalence claim from sampled inputs is needed.

The joint-zero promise remains essential: multiplying a nonzero original target
by a zero source destroys its value, so a norm guard alone cannot recover that
case. The repaired third-pivot projective D=0 chart has a different, genuine
flag contract and is not a removable instance of this fallback.

This result excludes the literal guarded closing in both supplied providers
and its exact zero/shift motif. It is not a general theorem excluding every
transformed guard elsewhere. The source findings plus the 50 positive full
matches are sufficient to reject this particular proposed saving. No decrease
in Q, T, local cost, or Public Score is claimed.

## Reproduce

Run from the repository:

```sh
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score5_dqi_guard_scan.py
```

The scanner reads the immutable whole candidate and writes only its own report
and isolated templates under
`/workspace/scratch/3815fb5fae06/score5_dqi_guard/`. It records source hashes,
template hashes, candidate hash, and complete match ranges. Its dependency on
the upstream Python emitters is an import; no upstream source was copied or
modified.
