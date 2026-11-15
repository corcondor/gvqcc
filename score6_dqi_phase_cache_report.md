# Live-product and nonlinear phase contraction on score5 DQI

## Result

No production rewrite was found in this bounded analysis. The verified DQI
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`
is unchanged. No new DQI score, global optimality, or universal lower bound
is claimed.

The new target was different from the previous common-wire pair scan:
if the current live registers satisfy `a*b = XOR_j d_j XOR k`, then

`(-1)^(a*b*c) = (-1)^(XOR_j d_j*c XOR k*c)`.

A CCZ can therefore become a network of CZ and Z gates, with no charged
Toffoli. A product may have been computed on another register or be hidden
in an XOR basis. The scan also looks for repeated CCZ phase functions across
nonlinear transformations inside a fixed condition-stack region.

## What was implemented

`score6_dqi_phase_cache_scan.cpp` processes the complete columnar KMB without
building tens of millions of gate objects. It tracks XOR/AND expressions,
complement identities and Boolean idempotence. Two discovery representations
are available:

- Structural product atoms with 1,024-bit linear signatures.
- 1,024 bit-packed Boolean evaluations with actual AND, exposing additional
  distributive identities that a product-atom representation can miss.

The second representation is a candidate filter, not a proof. Even an exact
match on all these evaluations would require an independent exact symbolic
or satisfiability certificate before rewriting the circuit. Rare predicates
can appear constant on a finite panel; such apparent zeros are not gate
reductions.

The final run preserves conditional-arm relations: PUSH snapshots the
incoming values, the executed arm is analyzed, and POP conservatively joins
different values with fresh symbols. Explicitly conditioned quantum writes
are also conservatively forgotten. CSWAP is modeled by its exact identity
`d = a*(b XOR c); b ^= d; c ^= d`, instead of discarding both target values.
HMR/reset clears its target, and classical condition versions are tracked.
Phase histories stop at every PUSH/POP. Thus no equality is inferred simply
because two instructions reuse a classical-bit number.

## Completed final scans

Both final scans processed all **58,868,734 operations**, including **363,654
CCX**, **12,240 CSWAP** and **7,000 CCZ**, on the actual Q889 artifact.

| Final method | Product-to-live-register hits | Repeated phase hits | Time |
|---|---:|---:|---:|
| Structural expressions, executed arms, exact CSWAP | 0 | 0 | 8.712 s |
| Boolean evaluation panel, live XOR spans, executed arms, exact CSWAP | 0 | 0 | 40.826 s |

The Boolean run considered the three two-factor choices at each CCZ:
21,000 queries in total. It solved 12,900 live-span systems and excluded
8,100 sparse or near-constant panel products (fewer than64 or more than960
ones among1,024 evaluations). It compared2,950 nondegenerate phase functions.
The excluded cases are unresolved by this filter, not proved irreducible.
Maximum recorded process RSS was685,568 KiB. The initial formal state allows
all quantum wires to be arbitrary, which is conservative for clean scratch.

The final source hash and complete commands are in
`score6_dqi_phase_cache_runtime_v5.json`. The two authoritative result files
are `score6_dqi_phase_cache_fredkin_structural.json` and
`score6_dqi_phase_cache_fredkin_truth_span.json`.

## Meaningful positive and negative controls

`score6_dqi_phase_cache_check.py` builds and parses six small native KMBs:
clean cached product, dirty accumulator, exact Fredkin round trip,
conditional-arm round trip, duplicate phase, and changed classical guard
version. Every expected discovery result passes. A separate enumeration
checks all16 basis/untouched-reference columns of the clean CCZ-to-CZ
identity, and finds four counterexamples to the unsound dirty-target variant.
These are optimizer checks, not additional full-decoder verification shots.

## Theory and remaining scope

The applicable viewpoint is nonlinear relational analysis: rewrite a phase
only when its controlling Boolean function equals a function available at
the replacement point, including classical control and measurement semantics.
See Amy and Lunderville, *Linear and non-linear relational analyses for
Quantum Program Optimization*,
<https://arxiv.org/html/2410.23493v1>.

This implementation is a specific, bounded analysis inspired by that
viewpoint. It is not the authors' Feynman optimizer and does not compute full
Gröbner bases. A global Boolean ideal analysis, newly synthesized nonlinear
features, rare-predicate certificates and algorithm-level changes remain
outside the completed result.

## Reproduction

```bash
g++ -O3 -std=c++20 -march=native score6_dqi_phase_cache_scan.cpp -o phase-cache-scan
./phase-cache-scan /path/to/e4/dqi.kmb structural.json --branches --fredkin --no-span
./phase-cache-scan /path/to/e4/dqi.kmb panel.json --branches --fredkin --truth --balanced
python score6_dqi_phase_cache_check.py --scanner /absolute/path/phase-cache-scan --workspace /new/controls --report controls.json
```

The control builder requires Kickmix. Production scans use only C++ and
read the original circuit without mutation.
