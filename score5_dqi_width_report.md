# DQI child-norm pebbling: implemented, locally narrower, not adopted globally

## Outcome

The retained-child inverse now has two executable variants. Borrowing one
child-norm bit lowers its peak by one qubit for 12 extra CCX per inverse.
Borrowing all six lowers its peak by six for 30 extra CCX per inverse. Both
variants preserve the existing inverse, zero-flag, and deferred measurement
phase contracts. The native component checks pass.

The six-bit variant was also spliced into the two exactly matched third-pivot
blocks of the verified `6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02`
tape. It removes those local 889-qubit peaks. **The whole tape still needs
889 qubits elsewhere, and adds 180 Toffolis. It is a research intermediate,
not a score improvement and not an adopted submission.**

The original input tape and all prior source files were left unchanged. This
branch did not run a whole-decoder native or official verification because
the remaining width makes the intermediate more expensive.

## Implemented resource tradeoff

| Circuit | Original | Borrow one bit | Borrow six bits |
|---|---:|---:|---:|
| Additional inverse helpers | 24 | 23 | 18 |
| Added CCX per inverse | 0 | 12 | 30 |
| Native pair width, including data/bank/flag | 73 | 72 | 67 |
| Native pair static Toffolis, including one phase probe | 389 | 413 | 449 |
| Third-pivot component width | 889 | 888 | 883 |
| Third-pivot component static Toffolis | 1,260 | 1,332 | 1,440 |
| Whole-tape width established here | 889 | not emitted | 889 |

The third-pivot chart contains three prefix inverses and three matched return
inverses. Thus its added count is exactly 72 or 180. The new gates are
unconditionally executed inside the matched chart blocks, so the added mean
count on identical inputs and measurement branches is also exactly 72 or
180. The benchmark's default binary-derived test seed can change the input
cohort; no independently measured whole-score delta is claimed.

For the six-bit intermediate, the complete static count is 382,896 →
383,076, the width remains 889, and the operation count is 58,868,730 →
58,872,726. Using the reference mean 382,068.47728515626 and the same error
repetition factor, its cost ratio is 1.0004711197356009, approximately
0.0471% worse. That is why it is not adopted.

The component report is `score5_dqi_width_component.json`. The independent
read-only review is `score5_chem_width_review.json` and its accompanying
Markdown file, owned by the other agent. The latter found no concrete defect
in the reviewed algebra, phase handling, or ownership, but explicitly did
not infer a full-decoder pass or global width reduction.

## Coherent identity and phase proof

The original matched inverse preserves these caller-owned bank registers:

- `original_norm`: 12 bits, the norm of the 24-bit entry source.
- `child_norm`: 6 bits, the quadratic subfield norm of `original_norm`.
- `child_inverse`: 6 bits, the reciprocal of `child_norm`, with inv0(0)=0.

At the original peak, `inverse_norm` adds 12 bits and the consuming
multiplication target adds another 12. The caller bank therefore occupies
24 bits while 24 additional helpers coexist.

Write the tower representation of `original_norm` as `(L,R)` over GF(64).
Then the preserved child is

\[
N(L,R)=L^2+LR+\delta R^2.
\]

The new emitter applies the exact norm XOR to one or all six child bits.
Because these bits already hold the same norm, they become zero coherently.
No measurement is added by this erase. `original_norm` is converted from its
polynomial coordinates to tower coordinates only during the norm XOR and
converted back immediately. Its value is unchanged.

For one selected output coordinate, the product term has the decomposition

\[
[LR]_k=\bigoplus_{i=0}^{5} L_i
  \left(\bigoplus_{j=0}^{5}[e_i e_j]_k R_j\right).
\]

The six parities are computed in place on the right operand and restored
after each CCX. The square contributions are linear CNOTs. Consequently a
one-bit toggle costs six CCX and no extra qubit. Erasing then restoring costs
12. For all six bits, the frozen rank-15 GF64 product is used once in each
direction, for 30 CCX total.

The exact schedule is:

1. Compute `inverse_norm`, then restore the polynomial encoding of
   `original_norm`, as in the original source.
2. Coherently erase the selected child bits from their still-live parents.
3. Allocate only 11 or 6 new temporary bits. Concatenate them with the 1 or
   6 borrowed child bits to form the original 12-bit consuming target.
4. For each source half, compute the product, swap it into the source, and
   HMR all 12 old-target bits. Each borrowed bit is zero after each HMR.
5. Free only the newly allocated temporary bits. The caller bank is never
   freed by the new emitter.
6. Pay the old-source masks using the new source half and preserved original
   norm, exactly as before.
7. Recompute the borrowed child bits from `original_norm` before that parent
   is measured or the child is used in the parent reconstruction phase.
8. Continue the original child-mask and reciprocal-norm cleanup unchanged.

During step 4, the new temporary bits enter with exactly the same zero value
as the old independently allocated target. Therefore, for each fixed HMR
outcome, the measured Boolean value and its phase are the same, under the
target-wire correspondence. Step 7 restores the exact child before all
remaining phase witnesses. This proves the replacement on arbitrary
coherent superpositions in the original component contract, including zero
through inv0, and with an arbitrary dirty zero flag. It is not an assertion
that the chart's existing finite-output domain has been enlarged.

No additional HMR, reset, classical allocation, or random event is introduced.
The complete classical instruction trace of each old/new chart half is
identical. The splicer asserts that trace equality and preserves every
original classical ID, including the three deferred six-bit child masks.

## Validation and source binding

The scalar norm-coordinate formula was exhaustively checked for all 4,096
pairs `(L,R)` in GF64². Native pair tests used a fixed public 512-input
fixture, including zero, the coordinate axes, boundary values, and uniformly
generated words. Both old flag values occur. Two fixed HMR seeds were used
for each of the original, one-bit, and six-bit variants.

The intermediate inverse is probed by an arbitrary classical linear phase
and a cubic quantum CCZ phase before the return. All six native runs had
zero source-restoration, dirty-flag, clean-scratch, or phase errors. These
are component checks, not exhaustive enumeration of 2²⁴ inputs or all HMR
outcomes. The general branch argument above supplies the broader identity.

`score5_dqi_width_binding.json` records unique exact opcode/operand matches
against the 6a tape under injective quantum/classical renaming:

| Part | Zero-based half-open source interval | Old operations | Six-bit operations |
|---|---|---:|---:|
| Prefix | `[17097498, 17126973)` | 29,475 | 31,473 |
| Return | `[54178102, 54213318)` | 35,216 | 37,214 |

Both boundaries have condition-stack depth zero. The data and owned-bank
roles agree between prefix and return, as do all saved child-mask roles.
The data/bank mapping is preserved. Clean temporary physical slots are
mapped into 864..882 for the six-bit chart. The full header remains 889
because untouched regions still address and require the higher slots.

The whole intermediate is:

`/workspace/scratch/3815fb5fae06/score5_dqi_width/borrow6_partial.kmb`

SHA-256:

`11a14e1c9c13c41345fca7cb3a7fe38966123bb97009d32fe66bb9143baf8054`

`score5_dqi_width_partial.json` pins the build and states its limited scope.
The original register packets and every operand-column byte outside the two
matched blocks are copied verbatim. The component build is derived from
Syed Asad Ali's Apache-2.0 source; its source copyright and credits are
retained in the new module.

## Why this is not yet a global width reduction

Two whole-tape streaming audits were performed. The first permits all
reset-separated zero gaps, including ABI gaps if they existed. It found no
unused quantum wire and no unconditional ABI reset. The second is stronger
for classical conditionals: it evaluates a PUSH arm and joins its final
state with the skipped arm only at POP. This recognizes conditional
compute→HMR cleanup that a per-instruction constant join misses. A wire is
released only if every skipped enclosing branch also has it zero.

The branch audit has no unsupported opcode on this tape and records 241,810
zero transitions. It still finds a conservative peak of 889. These counts
are scheduling certificates under this abstraction; they are **not a
semantic or information-theoretic width lower bound**.

After the six-bit chart patch, the first peak moves from original index
17,100,570 to intermediate index 18,499,201. Accounting for the inserted
1,998 prefix operations, this is original index 18,497,203. The original
2,140 conservative peak ranges become 2,128; peak-occupied operation count
falls from 9,491,306 to 9,477,084. The complete original range ledger is
`score5_dqi_width_peak_ledger.json`. All 326 nearby clusters have not been
individually bound to named source functions.

The next peak was inspected directly. Original interval
`[18496027,18502248)` is an unconditional rank-99 consuming GF24 product:
6,122 CX and 99 CCX, followed by 24 SWAP and 24 HMR. It is the
`direct_carry_arithmetic._adjoint_consume` stage of node 18's unit division.
The wire roles are:

| Role | Physical wires | Count |
|---|---|---:|
| Current selected unit | 432..455 | 24 ABI data bits |
| Retained carry / old target | 840..863 | 24 |
| Rolling quantum selection flag | 864 | 1 |
| Consuming-product output | 865..888 | 24 |

The immediately preceding controlled swaps use that same flag to select the
unit/source pair. This region has no retained `original_norm`/`child_norm`
witness to erase using the new identity. It needs a separate scheduling or
arithmetic construction. The previous hybrid tail emitter can remove all
but the last forward rolling flag for no added Toffolis, but it does not
remove the reverse flags, their consuming products, or the remaining seams.
That earlier result was not rerun or counted as a new global improvement.

Other unresolved families include norm/scalar-inverse helper peaks, gauge
normalization, reverse selected-unit products, and their boundaries. The
parallel investigations classified further exact scalar and reverse-product
blocks in `score5_chem_width_late_classification.json` and `.md`:
paired division `[26456255,26463192)` contains the two 42-T scalar consumes
`[26458248,26460684)` and `[26460684,26463120)`, while the later interval
`[35689634,35695903)` is another exact 99-T `_adjoint_consume`. The scalar
family has an unadopted park-factor/defer-phase proposal; the 99-T product
does not have the retained child-norm witness. Those findings must be
combined with a future full allocation proof
before advertising Q888 or Q883. The obsolete guarded-closing kernel is not
a valid shortcut: the sibling's exact scan found production matches only
for the already-unguarded kernel.

## Reproduction

Use the pinned Kickmix environment and the existing source tree. The check
script creates the exact component KMBs and native receipt in a new output
directory:

```sh
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score5_dqi_width_check.py --out /workspace/scratch/3815fb5fae06/score5_dqi_width/component_repeat
```

`score5_dqi_width_bind.py` takes `--baseline`, `--profile`, `--components`,
and `--out`; it requires a unique exact prefix/return match. The splicer
takes `--binding`, `--components`, `--borrow 1|6`, `--output`, and `--report`.
It refuses to overwrite the output KMB and explicitly keeps the whole
quantum width unchanged. The two C++ lifetime audits take an input KMB and
an output interval TSV and print their JSON result to stdout.

The manifest records source, receipts, component circuits, dependencies,
and the large scratch intermediate separately. No whole official job was
started, and this branch's files do not supersede the separately improved
Toffoli-count candidate being prepared by the root agent.
