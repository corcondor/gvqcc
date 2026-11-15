# score7: whole-phase resubstitution

## Result and scope

The new scanner found **zero production rewrite candidates**. It does not
change the accepted DQI binary and makes no new score claim.

The accepted input is `score5_norm_final/dqi.kmb`, SHA256
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.
The complete input has 58,868,734 operations, Q889, 363,654 CCX, 12,240 CSWAP,
and 7,000 CCZ. The scan took 25.5787 seconds.

## New search family

The previous score6 pass checked whether a *pair* of CCZ controls, such as
`a*b`, already existed in the live-wire affine span. This new pass tests the
**entire phase function** `a*b*c` against:

1. Every live wire, including its complement.
2. The affine span of every live wire plus one.
3. A product of two arbitrary live literals, optionally complemented.

An exact relation `a*b*c = XOR_i q_i XOR constant` would replace the CCZ by
Z gates and possibly NEG. An exact relation
`a*b*c = (q_i XOR u)*(q_j XOR v) XOR w` would replace it with CZ, Z and NEG.
All these replacement operations have zero Toffoli-like cost in this task.
The product need not match a named pair of original controls, so this is a
strictly different discovery query from the previous pair cache.

The implementation uses a 2048-column Boolean evaluation panel, retains
XOR/AND semantics, propagates Fredkin as
`delta = control*(left XOR right)`, and snapshots conditional-arm state.
At branch joins, changed values become fresh arbitrary values. Explicitly
conditioned writes are also conservatively forgotten. Every initial qubit is
arbitrary; no unproved clean-ancilla assumption is introduced.

These signatures are **discovery filters, never equivalence proofs**. A match
would need exact replay before any circuit rewrite. There were no matches.

## Rare predicates

Of 7,000 CCZ gates, 2,950 had panel Hamming weight between 64 and 1984 and
entered the complete affine/quadratic search. The other 4,050 were excluded
because a rare predicate can look identically zero on a finite random panel.
The result therefore does not exclude useful relations for those rare phases,
and is not an optimality result for the circuit.

## Validation

Six native KMB fixtures cover a live cubic value, a cubic value hidden in an
XOR, a quadratic replacement, an initially dirty target, a conditional arm,
and an explicitly conditioned write that must not be treated as unconditional.
All expected discovery results match.

The positive cubic-XOR replacement has an independent exhaustive comparison
of 64 basis/Kraus entries, including the measurement outcome and an untouched
reference bit. Four dirty-target counterexamples confirm why the clean-target
precondition cannot be dropped. The fixtures and the proof check pass.

## Reproduce

```bash
g++ -O3 -std=c++17 -Wall -Wextra score7_dqi_phase_resub.cpp -o phase_resub
python score7_dqi_phase_resub_check.py --scanner ./phase_resub \
  --workspace /new/fixtures --report /new/fixtures.json
./phase_resub /path/to/e4/dqi.kmb /new/discovery.json
```

The fixture builder needs Kickmix. The scanner needs only a C++17 compiler.
No official full verifier was rerun on the unchanged DQI input.

Evidence: `score7_dqi_phase_resub_scan.json` and
`score7_dqi_phase_resub_check.json`.
