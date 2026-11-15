# Generic inverse width: bounded source and ABI assessment

This is a source-level feasibility note for candidate
`6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02`.
It is not a general width lower bound and introduces no new candidate or run.

## The chart pebble has a specific retained-bank contract

The child-norm schedule in `score5_dqi_width_inverse.py` relies on a caller-owned
24-qubit clean bank. During the critical scalar products it retains the
original12-bit norm, its6-bit child norm, and the6-bit child reciprocal in that
bank, with inverseNorm12 separately live. A selected child-norm coordinate can
be erased from its preserved original-norm parents, used as a clean product
target, reset by HMR, and recomputed before its phase witness is needed. The
one-coordinate erase/recompute adds12 CCX per call. The sibling's native
component result concerns this particular ownership contract.

The generic production providers do not have that bank:

| Provider/stage | Simultaneously live helper storage |
|---|---|
| `gf24_nested_norm.emit_closing`, adjoint consume | temporary24 |
| Same closing, nested norm inversion | norm12 plus nested inverse helpers12 |
| Same closing, scalar consumes | reciprocalNorm12 plus temporary12 |
| `direct_carry_arithmetic.divide_deferred` | the same three independent peak families |
| `direct_carry_arithmetic.restore_with_shared_norm` | head/next adjoint temporary24, then inverse norm and scalar-product peaks |
| Production `quotient_phase84_mask_guard.inverse_closed` | reciprocalNorm12 plus nested inverse or product temporary12 |

`nested_norm_inverse.inverse_twelve_deferred` consumes the original norm into
its reciprocal and returns HMR masks of the old tower halves. It repays the
child masks while the original parents are still present, then erases/releases
the child reciprocal before the generic outer scalar-product stage. There is
no retained original child-norm bit at that later peak to reuse as in the chart
schedule. Adding an entire retained24-bit bank would not reduce the generic
peak.

The actual-binary guard audit found50 entire unguarded nested closing blocks;
the guard branch is not the extra quantum wire in these generic calls. That
audit is recorded in `score5_dqi_guard_scan.json`. The production closed inverse
is rebound by `after_v3/integration_v7/v7_pipeline.py` to
`after_v3/audit/retained_child/quotient_phase84_mask_guard.py`; its classical
all-zero-mask bypass adds no quantum flag and retains the same24-helper peak.

Therefore the chart schedule can be used where its existing clean-bank
contract holds. It cannot be substituted mechanically for the generic calls.
A global Q=888 implementation still needs a separate consuming-product
schedule, a cheaper norm/scalar schedule, or a proved caller-specific borrowed
wire/flag lifetime change. This note does not exclude such constructions.

## Prior work and current cost limit

`score_ancilla_report.md` already separates consuming GF24, nested inverse,
scalar-half consume, and reverse quantum-flag peaks. Its historical site counts
refer to the explicitly named older input, not a fresh count of6a. It also
records a forward-only hybrid flag schedule and a concrete full reverse-flag
reconstruction schedule costing3542 additional T; neither established a global
Q reduction. Those scans were not repeated here.

Using the current completed local official mean
`T=382068.47728515626`, at unchanged reliability factor the exact budget for
Q889→888 is:

\[
T\big[(889/888)^2-1\big] = 860.9991124600831.
\]

All required changes together must remain below that total to improve Q²T.
Shrinking one local peak does not by itself change the maximum circuit width.

## Node13 numerator-zero alternative

The already-frozen two-pivot repair in `score5_dqi_failure_report.md` was an
isolated structural repair of node13, not a repair installed at41 different
pivots. Its changed polynomial orientation must propagate to every remaining
residue view:21 pre-swap and20 post-swap interfaces, in both compute and
uncompute. The resulting bound is
`2*(21+20)*24 = 1968` additional CCX. The +48 native query component covers only
one such future-residue interface; using it alone would violate the decoder's
consistent polynomial-view ABI.

With current6a meanT, that known overhead alone increases Q²T by0.515091% at
Q889, or0.741349% atQ890. Predicate, alternate normalization, and flag-cleanup
costs are additional. For comparison, the saved local102400-shot confidence
calculation changes the reliability factor by0.459264% between zero and one
failure, or0.850158% between zero and two failures. The targeted known fixture
does not estimate a population failure rate. Thus there is no demonstrated
score benefit from this costly component, and no adoption is justified by its
single repaired known input.

The accepted6a candidate and all packaging artifacts remain unchanged.
