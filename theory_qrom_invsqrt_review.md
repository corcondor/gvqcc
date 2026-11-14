# Independent review of inverse-root reachable-domain screen

Reviewed 2026-11-15 Japan time. Reviewer: independent QROM task agent.

## Verdict after refinement fix

No correctness blocker was found for the recorded, pinned **no-rewrite** result. The initial review identified an incompleteness in the signature-only affine solver. The author then added counterexample-guided refinement, and this updated implementation was independently reviewed and checked against an exhaustive small coefficient oracle. **The identified false-negative gap is resolved in the current arbitrary-affine membership algorithm.**

The current saved full-domain result reports 1551 complete affine-membership queries, 64 counterexample refinements, at most 5 refinements in one query, and zero rewrites. This supports a negative conclusion for the specific gatewise affine replacement family on the explored entry domains. It remains neither whole-circuit optimality nor an exclusion of identities valid only on more restricted classical-condition domains.

Reviewed files:

- `theory_invsqrt_reachable.py`
- `theory_invsqrt_reachable_results.json`
- `theory_invsqrt_reachable_affine_results.json`

This review did not repeat the full-domain execution. It read the code/results, inspected the pinned KMB instruction set and conditional instructions, and subsequently ran a small adversarial coefficient-oracle check of the refined affine solver.

## What the recorded computation establishes

The source SHA-256 is `e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6`.
Its registered input is q0 through q21, in that order; the circuit has 46 qubits.

The full truth-table representation correctly masks out x=0 and includes exactly x=1 through x=3,133,452. The X, CX, CCX, SWAP and CSWAP data updates implement their Boolean semantics on that domain. HMR clears the measured/reset wire. General rotations, measurement instructions and classical operations are retained.

Both saved runs report completion, zero proposed rewrites, all final data restored, and 702 conditional joins whose full data truth tables agree exactly with the corresponding entry tables. These are observations of the saved runs, not a new verifier execution performed in this review.

Every accepted CCX, CSWAP or CCZ replacement must pass an equality of complete truth tables. The 256 input signatures cannot themselves justify a replacement. This is implemented correctly: signature matching is followed by a complete-domain equality test.

## Conditional execution

The pass explores each PUSH branch as taken on the complete entry domain and requires data identity at its POP. Nested branches can be treated inductively: when both the taken branch and skipped branch return identical data, later data values do not depend on that branch choice. Intermediate phase/classical effects need not vanish, because the pass retains those operations and gatewise data equivalence preserves their inputs.

This explores a superset of truly reachable branch/input combinations when classical conditions exclude some x values. Consequently it may reject useful rewrites valid only under a specific condition. This is conservative, rather than a false-positive source, for the current supported instruction set.

Light inspection of the pinned circuit found explicit `if` conditions only on:

| Instruction | Count |
|---|---:|
| PUSH_CONDITION | 702 |
| CZ | 541 |
| NEG | 27 |
| BIT_INVERT | 39 |

There are **no explicitly conditioned data-mutating gates** in this pinned input. That matters because the current generic X/CX/CCX/CSWAP handlers do not interpret an explicit `if`, and their replacement construction would not preserve such a suffix. The fixed source hash prevents accidental use on a different circuit containing those unsupported cases. Generalization to another input should add explicit guards or implement the missing semantics.

## Initial finding: the old signature-only solver could have false negatives

Write the full-domain linear map of candidate generators as A, and restriction to the 256 signature inputs as S. The initial version solved

\[
SAc=Sf
\]

for one coefficient vector c, then checked whether Ac=f. A failed full check does **not** imply that no full-domain solution exists. Another signature solution

\[
c'=c+k,\qquad k\in\ker(SA)
\]

may satisfy Ac'=f even when c does not. The initial code returned `None` without exploring that kernel.

For example, two available wire functions can agree on all signature inputs but differ elsewhere. If the target is the second function, the signature basis may retain only the first. The selected full-domain combination then fails even though the second wire itself is an exact one-term replacement. The old `max_terms>2` branch ran before the direct one/two-wire scan, so this type of missed match was not automatically recovered by the smaller search.

The `max_terms<=2` path does enumerate all signature-compatible one/two-wire candidates and tests each on the full domain; it does not suffer from this particular single-solution issue. It remains restricted to this small family and to the conservative branch-domain model.

Safe wording for that initial, superseded arbitrary-affine result was:

> The bounded signature-guided search proposed no replacement that passed complete-domain equality; it does not prove that no affine replacement exists.

## Resolution: complete counterexample-guided affine membership

The current implementation does not immediately reject a disagreeing signature solution. It chooses an exact input x where Ac and f differ, appends the corresponding bit of every full-domain generator and target to the local signature system, and repeats Gaussian elimination.

Every added counterexample either strictly increases the coefficient-matrix rank or makes the system inconsistent. With n generator columns and initial coefficient rank r, at most n-r independent additions are possible, followed by at most one inconsistency witness. The nonzero constant generator ensures r>=1, so at most n<=47 counterexamples suffice here; the implementation's slightly looser loop guard is safe.

- If a full-domain equality is accepted, the returned coefficients are an exact witness.
- If the finite restricted system becomes inconsistent, no full-domain coefficients can exist.
- A nonterminating sequence of counterexamples is impossible by the rank bound.

The implementation preserves the full generator values, appends each witness at a new high signature bit, and correctly carries coefficient masks for the constant and all eligible wires. No target wire excluded by the rewrite rule is reintroduced by refinement.

### Independent small-oracle check

`theory_qrom_invsqrt_refinement_review.py` extracts the actual `affine_match` function from the reviewed source via AST and compares it with exhaustive coefficient enumeration. This is independent of the Gaussian elimination used by the function. It uses six truth-table inputs but only two signature inputs, deliberately forcing signature collisions.

| Check | Result |
|---|---:|
| Generator sets | 12 |
| All target truth tables per set | 64 |
| Total decisions | 768 |
| Exact members / nonmembers | 296 / 472 |
| Counterexample refinements exercised | 1580 |
| Largest refinement count | 4 |
| Agreement with exhaustive coefficient oracle | All 768 |

The reviewed source hash was `b90affba279067e77e7ccf120fb638fa74dfde8c0243923c35afc4fd84e4f60c`. Results are in `theory_qrom_invsqrt_refinement_review.json`.

### Updated full-domain record

The subsequently inspected `theory_invsqrt_reachable_affine_results.json` records completion on all 3,133,452 permitted x values, 702 data-identity joins, **1551 membership queries, 64 refinements, maximum 5**, zero rewrites and full final data restoration. Runtime recorded by the author is 1.270829703 seconds. This reviewer read that result rather than rerunning the full circuit.

## Additional scope limits

- The 702 joins prove restoration of data functions. They do not independently prove correctness of the baseline's inverse-square-root phase, cancellation of every measurement phase, approximation accuracy, or official score.
- Preservation of measurement/rotation instructions supports equivalence of an accepted gatewise replacement because its data inputs are proved identical; unchanged instruction text alone would not be sufficient without that data proof.
- `peak_simultaneously_nonzero_functions=46` means each of 46 wires represents a function that is nonzero somewhere at that program point. It neither says all 46 bits are 1 on one input nor proves a 46-qubit lower bound. Alternative encodings and changed schedules remain possible.
- No candidate was emitted in either recorded run, so there is no new inverse-root submission or score improvement to claim.

## Summary suitable for the combined report

The pass tracked all 3,133,452 permitted inputs, checked 702 data-identity joins, and found no exact replacement in 1551 complete affine-membership decisions. The initial signature incompleteness was corrected using 64 exact counterexample refinements. The resulting exclusion applies to the specified single-gate affine replacement family on the explored entry domains; it does not establish global optimality or rule out identities exploiting additional classical-condition restrictions.
