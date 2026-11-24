# Phase-derived shared hub, 2026-11-24
Pinned parent: PR #28, 49263f69b474b686fd92969b03c3374d188ebddd; source KMB SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03. PR #24 used a different reference; do not mix indices without byte-level mapping.

## New actual-gate result
Ten concrete original gate lists (8288, 8400, 8512, 8624, 8736, 8848, 8960, 9072, 9184, 9296) have an identical initial HMR correction structure on four spectator wires. All contain q14; both translation directions (q14 and d), (q14 and b and c) have derivative 1 and are unused by subsequent arithmetic within their respective slice.
f(a,b,c,d)=a^b^(a&b)^(a&c)^(b&c)^(b&d)^(c&d).
u=a^d; f=a^g, g=b^u^((b^u)&(c^u)).
Assume source entry q35=f and q36=0. Measure the redundant transformed q14 coordinate with Clifford phase correction, keep old q35 as the central encoded spectator, reuse q14 for first carry, and perform the remaining six operand-carrier stages. Preserve events 0 and 1 as arbitrary outcomes (unlike PR28's normalized event 1); remaining 2..7 are normalized zero as before. No claim about whole-program HMR elimination without its separate phase ledger.
Ten open charts: 80 source CCX, 150 PR28 CCX, 140 new open CCX, 150 including restoration. 10,485,760 independent active basis assignments, all values, two phase coefficients, and decoded outputs match. Other spectator wires not touched. This is a conditional local exact check on the gate lists in PR28, not on native source KMB bytes or all legal reachable states. No closed-cost reduction, no full 36Q oracle or official score. Generated native-style gate lists are in the receipt; clearEvent is the same normalized classical semantics as PR28, not a native KMB opcode.

## Deeper transition screening
45 pairs of actual charts, both translation directions per chart, 180 direct transports on identical logical spectator states; all have degree 3 and nonlinear-output rank 2, so none can be implemented by a single affine-conjugated CCX. 36 adjacent direction combinations included. This is a bounded exact result and excludes the original intervening gates. Do not repeat the same one-shear search with more seeds. Actual gaps must be recovered from source KMB; joint conjugation/changed arithmetic can evade this bound. Don't claim 10 CCX savings in an independently callable/closed circuit.

## Shared next work
- PR #25–27 owners: export exact original instructions [8350,8400), [8462,8512), ..., [9246,9296), plus chart/legal-entry certificates for q35=f and q36=0; export native complete 37Q KMB with pinned hash and verify matching command indices. Cross-gap compiler should carry chart and phase ledger together, and score closed cost, not open savings or coverage.
- PR #23 ANGLE owners: phase-derived directional chart can be applied only where HMR correction coefficient is zero on reachable states and independent bank ABI is preserved. Don't reuse withdrawn PR22 or count unclosed hub savings.
- PR #28: new proof model preserves two arbitrary HMR outcomes; integrate only after CI and global coefficient checks. Full source byte verification and exact original/candidate KMB remain required.
- PR #27 phase ledger and Pareto receipts are the baseline; no source or main modification.

References: https://arxiv.org/abs/2503.09356 (offline combinatorial search inspiration), https://github.com/google-deepmind/formal-quantum-computation (formal candidate checking inspiration). QAOA is not a submitted gate and we do not claim a DeepMind agent replication.

Reproduce from repository root:
```sh
node research/invsqrt36_nonlinear_lending/phase_derived_hub.cjs
node research/invsqrt36_nonlinear_lending/phase_chart_transport.cjs
cd research/invsqrt36_nonlinear_lending/lean
lean PhaseDerivedHub.lean
```
Lean source generated; CI pending until an actual successful Actions run is observed. Do not merge until full official validation and score improvement.
