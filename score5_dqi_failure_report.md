# Active numerator-zero repair: implemented two-pivot component

## Result and adoption status

`score5_dqi_failure_twopivot.py` implements an alternate chart at public pivot
13 followed by pivot 14. The exact classical polynomial algorithm now takes
the known weight-31 case through the correct terminal state and reconstructs
the original numerator and locator exactly. The repaired rule selects a chart
from the actual remainder being zero, with no input identifier or verifier
seed in the algorithm. It also passes 128 fixed independent physical cases.

A genuine reversible quantum component implements the corresponding query
matrix. Native Kickmix checks of 4,096 inputs pass for its forward values and
for a compute–phase-probe–uncompute circuit, with zero value and phase errors.
The circuit contains only reversible classical gates and diagonal probes;
there is no sampled measurement-dependent phase debt in this component.

**This is not an improved full decoder candidate.** The straightforward
integration is too expensive: the query propagation alone adds 1,968 CCX,
and one retained flag would raise the naive whole width from 889 to 890.
First-pivot selection, synthesis, and flag retirement are additional costs.
There is no full-decoder KMB or official-verifier receipt for this experiment.
The existing completed third-pivot denominator-zero patch was not modified
or reimplemented.

## Exact polynomial rule

An ordinary step at irreducible public quadratic q_i is

```
P_i = (D mod q_i) / (N mod q_i)
(N,D) <- ((D + P_i N)/q_i, N).
```

When `N mod q_13 = 0`, coprimality ensures `D mod q_13 != 0`. Swap N and D
before step 13. Its head is then zero, and its output pair is `(N/q_13, D)`.
Execute ordinary step 14, then swap the pair back. Writing P for its head,
the two-step output is

```
(N/q_13, (D + P*(N/q_13))/q_14).
```

If the original degrees were at most `(r-1,r)`, the output degrees are at
most `(r-3,r-2)`, exactly the ordinary two-step bound. The branch is represented
by one retained flag. Reversing the two swaps and ordinary polynomial steps
recovers the input pair exactly, without discarding a zero-source product.

The branch requires `(N/q_13) mod q_14 != 0`; a numerator divisible by both
quadratics needs another chart. The complete construction also retains the
ordinary nonzero-numerator assumptions at other active pivots. The implemented
checks expose these conditions and never count a failed condition as repaired.

## Query component and resources

With `M_i = [[P_i/q_i,1/q_i],[1,0]]` and S the coordinate swap, future residue
queries use `S^f M_14 M_13 S^f`. The component calls the unmodified upstream
99-CCX query twice and adds two controlled 24-bit swaps. Both forward and
reverse restore the head registers and the flag.

| Quantity | Value |
|---|---:|
| Ordinary two-query cost | 198 CCX |
| Alternate-chart query component | 246 CCX |
| Component forward + return | 492 CCX |
| Test circuit including phase-probe CCZ | 493 Toffoli-equivalent |
| Component width | 97 qubits |
| Native forward cases | 4,096; zero value/phase errors |
| Native phase-probe round trips | 4,096; zero value/phase errors |
| Whole query propagation increment | 1,968 CCX |
| Naive whole width | 890 qubits |

There are 21 future residue queries requiring the pre-pivot swap and 20
requiring the post-pivot swap. Both traversal directions therefore cost
`2 * (21+20) * 24 = 1968` extra CCX, before synthesis and selection.
Quantum conditional gates have this cost on every execution; the rarity of
the branch does not give a classical-mask mean-cost discount.

An alternative `N <- N + f D` shear gives first head 1 on the exceptional
branch but still needs a final orientation swap and a `P + q_13` polynomial
correction. A 24-bit controlled swap already costs 24 Toffoli-equivalents in
Kickmix, so merely replacing it by a controlled XOR does not reduce that count.
No claim is made that 1,968 is a lower bound over all possible architectures.

## Reproduction and scope

```
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score5_dqi_failure_twopivot.py
```

The JSON result is `score5_dqi_failure_twopivot.json`. The actual native
component circuits are saved under
`/workspace/scratch/3815fb5fae06/score5_dqi_failure/` as `query_prefix.kmb` and
`query_roundtrip_phase.kmb`.

The independent polynomial reference is the unchanged upstream
`night_c27/census/reference.py`, SHA256
`a43a7dbf3ef0cb02f8660067a0067c603cf39fe7a552584c3fc9bc228f501aa6`.
The native component imports the unchanged `raw_query_extractor.query_step`.
The physical fixtures come from the existing `dqi_rare_failure_admission.json`.
No old artifact, scoring salt, submission, or browser state was changed.
