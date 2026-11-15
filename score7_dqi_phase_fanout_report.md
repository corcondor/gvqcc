# score7 DQI: bounded phase-aware fanout contraction

## Result

No candidate was found, and the accepted DQI binary was not changed.
The first and only full pass completed in **1.268 seconds**, with 648,560 KiB
reported child peak RSS. It scanned all 58,868,734 operations of the accepted
e4 circuit, including 363,654 CCX, 7,000 CCZ, and 593,412 diagonal gates.

The source was hashed after the scan:
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.

This is a new different-target search, complementing the same-target
involution scan. It permits diagonal phase gates on the moved target,
which the earlier pure-commutation fanout optimization treated as barriers.
It does not claim that an earlier accepted contraction was rediscovered.

## Exact rewrite

For two Toffolis with identical controls and different dirty targets,

`CCX(a,b,t); CCX(a,b,u)`

equals

`CX(t,u); CCX(a,b,t); CX(t,u)`.

The two targets may have arbitrary values. The new scanner allows the first
CCX to move to the second across diagonal gates and other commuting work.
Moving it across a phase polynomial P requires the correction
`a*b*(P(t=1) XOR P(t=0))`, in the Boolean sign-phase algebra. In particular:

- Z(t) gives the free Clifford correction CZ(a,b).
- CZ(t,c) gives CCZ(a,b,c), reducing to CZ(a,b) if c is a or b.
- CCZ(t,c,d) generally gives a four-variable phase, rejected unless repeated
  controls reduce its degree.

Correction monomials are XOR-cancelled using physical wire write versions
and classical guard versions. A remaining cubic correction may cancel an
existing matching CCZ inside the interval. A proposal is accepted only if
the resulting native Toffoli-like count strictly decreases.

The first CCX is deferred rather than deleted outright, so writes to its
target that commute with it can remain inside the interval. Any non-phase
use of that target as a control is conservatively a barrier. The two quantum
controls must have no writes in the interval. PUSH/POP boundaries are barriers;
explicit classical guard writes are tracked. The scan never silently assumes
that a reused measurement bit retains its earlier value.

## Bounded search counts

The pass considers the latest **32 CCX records for each physical control pair
and explicit guard**, with a maximum gap of **65,536 operations**. Repeated
records of a target are reduced to its latest occurrence. It does not use
sampled signatures or infer nonlinear equality of changed controls.

| Counter | Number |
|---|---:|
| Earlier records inspected | 8,048,967 |
| Same-target records excluded | 2,768,848 |
| Superseded target records excluded | 3,523,926 |
| Gap limit rejections | 564,625 |
| Condition boundary rejections | 26,814 |
| Quantum control write rejections | 1,164,730 |
| Non-phase target use rejections | 24 |
| Eligible pairs | 0 |
| Profitable candidates | 0 |

All pairs were excluded before the phase-cost stage. Thus the result does
not say that the circuit's phase corrections are intrinsically expensive;
it says that no suitable pair with the required stable controls and target
usage survived this bounded structural search. Algebraically restored
controls, longer distances, and new shared predicates remain outside scope.
No widening pass was performed.

## Positive and negative controls

`score7_dqi_phase_fanout_check.py` creates ten small KMB fixtures and runs the
compiled scanner on each. Four positive fixtures cover a crossed Z, a
control-overlapping CZ, cancellation with an existing CCZ, and a commuting
X write to the dirty target. They produce the expected savings of one or two
Toffoli-like gates. A separate scalar interpreter applies the emitted patch
and checks **80 complete dirty-input basis/phase columns** exactly.

Six negative fixtures check a non-saving cubic correction, a quartic
correction, a target used as a control, a changed quantum control, a changed
classical guard, and a PUSH/POP boundary. All correctly return no candidate.
These are small synthetic controls, not benchmark improvements.

No new official DQI verifier run is warranted because no candidate was
emitted. The existing official full verification for the unchanged binary
remains the relevant receipt. No submission was made.

## Reproduction

```bash
g++ -O3 -std=c++17 score7_dqi_phase_fanout.cpp -o /tmp/score7_dqi_phase_fanout
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score7_dqi_phase_fanout_check.py --scanner /tmp/score7_dqi_phase_fanout --out /tmp/score7_fanout_controls
/tmp/score7_dqi_phase_fanout /workspace/scratch/3815fb5fae06/score5_norm_final/dqi.kmb /tmp/score7_fanout.json
```

The C++ scanner is standalone and consumes KMBv2 directly. Its parsing and
write-version approach are adapted from the separately implemented
`score7_dqi_phase_commute.cpp`; the fanout rewrite, existing-CCZ cancellation,
and tests are distinct. `score7_dqi_phase_fanout.json` contains the actual
pass receipt, and `score7_dqi_phase_fanout_controls.json` contains the exact
control results. The manifest binds these files to their source hashes.
