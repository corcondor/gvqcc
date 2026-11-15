# Special symmetry audit of the submitted DQI821 circuit

## Result

The actual submitted DQI circuit, SHA256
`821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3`,
contains the previously studied structured multiplication kernels. A new
read-only scan checked the full source hash, every opcode, and every ordered
qubit operand under an injective wire renaming. It did not merely search gate
counts or infer kernels from a different candidate's filename.

| Exact kernel | Occurrences in DQI821 | CCX per occurrence | CX per occurrence |
|---|---:|---:|---:|
| GF(2^12) product accumulator | 3,823 | 42 | 1,276 |
| GF(2^24) symmetric inner product accumulator | 1,376 | 99 | 6,098 |

There are **5,199 exactly matched blocks**. The scan took 63.7 seconds and
used compact opcode bytes and memory-mapped operand columns. Production KMB
files, Kaggle artifacts, and remote repositories were not modified.

The first GF12 match is original operation interval `[11153938,11155256)`:
inputs q0..q11 and q12..q23; arbitrary accumulator q840..q851.
The first GF24 inner match is `[11212889,11219086)`:
inputs q0..q23 and q72..q95; arbitrary accumulator q840..q863.

These measurements supersede the earlier unqualified suggestion that all
important EEA products are generic 78-CCX twelve-bit multipliers that can
automatically become 54-CCX Karatsuba products. That suggestion did not match
these actual kernels.

## A real conjugation symmetry, and what it buys

The existing representative physical EEA product is
`z ^= conjugate(a)*b` in the quadratic extension
GF(2^12)[t]/(t^2+t+2048). Its conjugation is

`C(a0+a1*t) = (a0+a1)+a1*t`.

It is an involution implemented by twelve CNOTs. Rechecking the stored
99-term tensor gives `u XOR ((u AND 4095) << 12) == v` for all 99 factor
triples. Thus its two input factors really become symmetric after this
linear change of coordinates.

The previous exact CPR construction exploits this symmetry: 6,122 CX become
1,535 CX including both twelve-CNOT conjugation layers, while 99 CCX remain.
The inner kernels now matched in DQI821 have 6,098 CX, excluding those outer
layers. GF12's corresponding exact routing uses 337 CX instead of 1,276,
while retaining 42 CCX. The existing proofs include arbitrary initial
accumulators, restored inputs, and phase, not only zero targets.

This supports applying the exact routing identities to DQI821. It does
**not** establish a new score gain: Q and T remain unchanged. Changing the
field basis or applying Frobenius to every tensor axis is an invertible
linear coordinate transformation and cannot by itself lower bilinear rank.
It can expose a cheaper CNOT route or an additional relation between inputs.

## New shared-operand target found in the real circuit

The scan found 3,868 neighboring matched-kernel pairs sharing a field input.
For 1,191 pairs both inputs use the same registers, but intervening operations
block the simple claim that the same product can be reused. There are zero
same-both-input pairs passing the conservative unchanged-input, pure-CX/CCX
gap rule. This is a restriction of this scan, not a proof that a larger
measurement-aware rewrite is impossible.

There are **193 directly adjacent GF12 pairs** with a common operand and
zero intervening instructions. For every one, all 60 wires across
`a,b,c,z1,z2` are distinct. In particular, the first product's output is not
the second product's input. Thus these windows implement exactly

`(a,b,c,z1,z2) -> (a,b,c,z1 XOR a*b,z2 XOR a*c)`.

They use 84 CCX in the present construction. The two circuits' inherited
condition is unchanged because no condition-stack instruction lies between
them. All placements and actual wire lists are recorded. Some eligible
windows overlap; interval packing selects 141 disjoint windows. Multiplying
a hypothetical saving by all 193 would therefore overcount simultaneous
replacement opportunities.

The combined tensor has dimensions 12 x 24 x 24. An independent integer
field oracle checked all 576 padded basis pairs. It has 84 distinct
input-product forms; the three paired-factor ranks are all 84. Therefore
there is no repeated AND product to remove directly, and deleting a term
while fixing its other two factors is obstructed. This is not a proof that
the joint tensor rank is 84.

## Bounded joint tensor searches actually executed

The existing pinned, unmodified Polytof BASE implementation was used through
the repository's deterministic drivers. No external model was claimed or
used. Each completed path was checked against the complete tensor
coefficient table, and the depth driver separately checked its best result.

| Problem and schedule | Paths x step cap | Largest visited rank | Best rank | Successful flips |
|---|---:|---:|---:|---:|
| GF12 shared-a pair, periodic plus | 32 x 200,000 | 102 | 84 | 6,400,000 |
| GF12 shared-a pair, explicit +6 excursions | 32 x 1,000,000 | 90 | 84 | 32,000,000 |
| GF8 shared-a pair, explicit +3 excursions | 64 x 1,000,000 | 15 | 12 | 64,000,000 |

The GF8 subproblem matters because the installed GF12 decomposition evaluates
at seven GF8 points, with six products per ordinary GF8 multiplication. A
valid 11-product shared-a GF8 pair would give a 77-product shared-a GF12 pair
by composition. **No such 11-product construction was found.**

Total search time was 22.64 seconds. There were 312,484 successful plus moves
and 102,400,000 successful flips. These are actual operations, not proposals.
This bounded failure is not global optimality or a reason to declare the
competition saturated. It establishes an exact larger target and a concrete
search baseline without inventing a gate reduction.

## Files and reproduction

`symmetry_dqi_20261115_scan.py` reproduces the exact DQI821 matching and
alias checks. The full scan is also stored as
`symmetry_dqi_20261115_scan.json.gz`; the uncompressed JSON is regenerable.
`symmetry_dqi_20261115_joint84_placements.json` lists all 193 qualified
windows. `symmetry_dqi_20261115_joint84_certificate.json` identifies the
combined tensor and exact oracle checks.

The two GF12 shared-a input-output triples are obtained from the original
42 triples `(u,v,w)` as `(u,v,w)` and `(u,v<<12,w<<12)`. They are embedded
in 24-bit axes with the high twelve bits of the first axis always zero.
GF8's corresponding construction uses shifts by three.

Search commands, after compiling the existing drivers as documented in
`theory_bilinear_report.md`, are:

```sh
polytof-driver symmetry_dqi_20261115_joint84_input.txt symmetry_dqi_20261115_joint84_search.json 32 200000 127 20261115
polytof-depth symmetry_dqi_20261115_joint84_input.txt symmetry_dqi_20261115_joint84_depth6.json 32 1000000 1000 6 20261115
polytof-depth symmetry_dqi_20261115_gf8_joint12_input.txt symmetry_dqi_20261115_gf8_joint12_depth3.json 64 1000000 1000 3 20261115
```

## Separate gauge-sort candidate

`score3_gauge_sort.py` exploits a different symmetry: a classical residual
label can be shifted together with the matching syndrome phase compensation.
Its full-width integration includes all twelve label bits, 2,126
classically controlled CZ gates, inverse shifts, scale restoration, and
pivot clearing. The exact mode selector uses only classical bits; reversible
quantum-gate costs do not apply to its private classical sort workspace.

Maximizing zero masks can lower the conditional scan's Toffoli count. The
existing paired classical study predicts roughly 20.3 Toffolis per shot
relative to gauge128, a small change against approximately 382,000 total.
Selector correctness and pointwise scan monotonicity do not replace complete
decoder value/phase verification or the error-dependent repetition factor
in the competition cost. That candidate's full qualification is separate
from this symmetry audit.
