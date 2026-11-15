# Exact simultaneous sign gauges of the five conserved ANGLE tags

## Result

The submitted score2 table admits a larger exact sign symmetry than the earlier
single-root-MSB experiment. All five conserved tags can be assigned arbitrary
Boolean values independently at each of the 1,220 addresses while preserving
the represented vector up to overall sign. A GF(2) solve constructs the required
changes to all 75 ordered Givens angles coherently.

The zero-tag representative changes 27,084 of 91,500 words. Reconstructing every
vector with the official mathematical implementation gives maximum difference
from the predicted signed original of `6.661338147750939e-16`. The experiment
also solved the five unit-tag representatives, with residuals below `7.8e-16`.
The constraint matrix is independent of the desired tag values; solvability at
zero and the five basis values proves solvability for all 32 tag assignments by
GF(2) linearity at every address.

These are equivalent physical coefficient tables, not improved measured
circuits. No matching KMB family, new official full-circuit PASS, or Toffoli
reduction is claimed by this calculation.

## Exact integer construction

For a word `w` representing angle `pi*w/128`, choose bits `s,k` and set

\[
w'=(-1)^s w+128k\pmod{256}.
\]

At an ordered tree edge `(p,c)`, the child starts at zero. If the incoming
parent has relative sign bit `z`, the new parent and child signs are respectively
`z XOR k` and `z XOR k XOR s`. Sines and cosines only change signs, so all exact
zeros and magnitudes are preserved. Requiring the final signs of the nonzero
coordinates to equal one shared sign bit therefore preserves `u u^T` exactly.

For the stored tag `t(w)=bit6(w) XOR bit7(w)`, direct integer arithmetic gives

\[
t(w')\oplus t(w)=k\oplus s\,[w\bmod128=64].
\]

Substituting the desired tag into this identity eliminates `k`, leaving a
linear system in the 75 reflection bits and one final global-sign bit. Exact
zero-support propagation uses only tests `w mod128 == 0` and `==64`; there is no
floating-point tolerance in the constraints. The script verifies every solved
equation before the numerical reconstruction cross-check.

The existing tags are confirmed to be

\[
(a_0a_1,a_0a_2,a_1a_2,a_0a_3,a_1a_3)
\]

for all valid addresses, repeated across all fifteen batches. The current
loader retains these nonlinear address functions in its output wires and uses
them as cached features. They are a deliberate part of the circuit structure.

## Why this is not automatically a large gate reduction

The zero-tag first load has binary output rank 35 instead of the original 40.
Every later transition already has rank 35 in the original family, because the
five tags are conserved. All fourteen transitions still have rank 35 after
the gauge change. Thus this symmetry does **not** remove five independent
functions from each of fifteen batches. Nor is an output-rank drop a proof of
an equal Toffoli drop.

The gauge also changes many low bits through two's-complement reflections.
Those changes are not generally XOR-only rewrites. Removing the original tags
also removes five useful address products from the loader's live interface.
The target representative and its circuit must therefore be synthesized
together; minimizing the word table's apparent complexity alone is unreliable.

The actionable new search space is a five-bit address-dependent tag choice,
plus zero-coordinate sign freedoms, constrained by exact vector invariance.
It can be supplied to a future loader synthesizer without spending the
20 mHa approximation budget. Existing loader/scratch/forward/reverse/HMR-phase
contracts remain mandatory. This report supplies the exact feasible target
family and a reproducible small computation, not a score-improving submission.

## Evidence and reproduction

- Source NPZ SHA256:
  `5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`.
- Implementation: `symmetry_chemistry_20261115_tags.py`.
- All-address results and table hashes: `symmetry_chemistry_20261115_tags.json`.
- Runtime: approximately three seconds, single-threaded numerical libraries.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python symmetry_chemistry_20261115_tags.py
```

The script writes only this experiment's JSON. It does not modify the source
NPZ, loaders, submitted ZIP, or any remote state.

## Measured follow-up: compile the equivalent table

The official `angle_k_reference_circuit.py` was reused to build all fifteen
loaders for both the original and zero-tag tables. The zero-tag family's
36,600 reachable forward/reverse transitions passed the existing exact checker,
including selection restoration, zero scratch, and cancellation of every
formal HMR phase variable. This is an actual in-memory compiled family, not a
gate-count extrapolation. It was not written as a new submission because its
cost is worse:

| Family | Loader CCX per pass | Loader maximum Q | CX per pass |
|---|---:|---:|---:|
| Existing optimized score2 family | 4,033 | 128 | Separate existing manifest |
| Original table, official generic QROM | 18,270 | 61 | 382,213 |
| Zero-tag table, official generic QROM | 18,270 | 61 | 382,245 |

Each generic loader has 1,218 CCX. The smaller per-loader quantum workspace
does not reduce the complete chemistry width, because the other workspace
requirement already dominates. Holding the rest of the score2 construction
fixed, replacing its loaders would raise total Toffoli cost from 14,728 to
`14,728 - 2*4,033 + 2*18,270 = 43,202`.

A descriptive ANF comparison used zero for the 828 unspecified addresses of
each 11-bit table. Both completions have 2,036 nonzero nonlinear monomial
coefficients per batch, across all fifteen batches. The sum of coefficient
bit weights is 578,108 before and 578,204 after normalization. These describe
one chosen completion; they are neither optimal synthesis results nor
Toffoli lower bounds. They provide no positive compression signal for this
particular canonicalization.

The general compiler is a unary-iteration QROM, not the specialized 4,033-CCX
synthesizer. Existing local tools for that family optimize or patch its current
products and do not synthesize an arbitrary new angle table at a comparable
cost. Preserving the useful output feature cache while optimizing the gauge
and shared product network together remains necessary for this direction.
The zero-tag generic family is therefore rejected as a score candidate.

Evidence: `symmetry_chemistry_20261115_compile.py` and
`symmetry_chemistry_20261115_compile.json`. Runtime was 3.85 seconds with
47.15 MiB peak RSS. The compiler SHA256 is
`aa32268dae7ad46cabd9fe3b620880cdd92909a32b6ca51c4b22da155e14ec7f`.
