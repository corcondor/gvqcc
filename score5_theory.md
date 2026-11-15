# Theory used in the score5 contractions

This note separates the implemented rewrites from source-local research that
did not lower the complete decoder's cost. It does not claim that a generic
optimizer or a paper's benchmark gains transfer unchanged to this circuit.

## 1. Factor repeated Boolean products before unitary decomposition

For arbitrary, possibly dirty, bits a,b,c,t,

```
CCX(a,b,t); CCX(a,c,t)
    = CX(b,c); CCX(a,c,t); CX(b,c).
```

Both sides implement t ^= a(b XOR c) and restore the controls. There is no
relative phase. The pass moves the first CCX only across individually checked
commuting operations, including measurements on disjoint wires. Eight pairs
in the real decoder were replaced. The independent review checks all basis
columns, each crossed instrument, and every changed operand in the final KMB.

The cost model charges Toffoli-like gates and quantum width. Trading two CX
for one CCX therefore lowers its arithmetic cost. Merely deleting CX gates
without changing these charged resources would not produce this gain.

Files: `score5_dqi_fanin.py`, `score5_dqi_fanin_scan.cpp`,
`score5_dqi_failure_fanin_review.py/.json`.

## 2. Move a measurement before a final unused write

The X-basis measurement/reset Kraus operator is M_m = |0><m_X|. For any
Boolean function f of the other wires,

```
M_m X_t^f = (-1)^(m f) M_m.
```

Consequently, a final CCX targeting t, followed eventually by HMR(t), can be
replaced by an earlier HMR(t) and a CZ conditioned on its outcome. Every
intervening instrument must be independent of t. The correction is emitted
at the original CCX position, so its controls have the right values even
when later arithmetic changes them.

This is the interval-MBU structure described by Yang and Yuan, **MBUndo**,
arXiv:2611.02345v1 (2026), sections 2.3 and 4.2. Their compiler analyzes
ancilla lifetimes, measures after a wire's last use, and replaces its later
XOR writes with phase corrections at their original positions. Here the
existing HMR supplies the endpoint; our strict pass needs no assumption that
the target held zero before its last write.

Primary paper: <https://arxiv.org/html/2611.02345v1>

The two actual decoder intervals contain many uses of the old destination
classical bit: respectively 51 reads/2 writes and 167 reads/224 writes. The
implementation therefore allocates a fresh outcome bit and copies it to the
old bit only at the original HMR position. Publishing the outcome earlier
would be wrong. The exact emitted copy is BIT_STORE0 followed by
BIT_INVERT_IF; it is checked against the binary opcode table.

This removes two more unconditional CCX, keeps the HMR count and Q889, and
adds two classical bits. Minimal native verification and a separate
whole-binary instrument review pass. The completed official receipt, when
present, is `score5_dqi_final_full_verification.json`.

Files: `score5_dqi_hmr_tail.cpp/.py`,
`score5_dqi_hmr_independent_review.py/.json`.

## 3. Recompute a small witness to borrow its storage

Parent, Roetteler and Svore's **Reversible circuit compilation with space
constraints** (2015) uses dependency analysis and reversible pebbling to
trade recomputation for fewer live temporary values. Reqomp, by Paradis,
Bichsel and Vechev (Quantum 8, 1258, 2024), synthesizes uncomputation under
ancilla constraints while considering the gate/space tradeoff.

Primary sources:

- <https://arxiv.org/pdf/1510.00377>
- <https://quantum-journal.org/papers/q-2024-02-19-1258/>
- <https://quantum-journal.org/papers/q-2024-02-19-1258/pdf/>

Our concrete application retains the parent GF(2^12) norm and temporarily
uncomputes one or all six bits of its child GF(2^6) norm. That storage then
holds a multiplication output. After HMR resets the borrowed storage, the
child norm is reconstructed before the original phase witness needs it.
One selected norm coordinate has a six-product bilinear representation;
erasing and restoring it costs twelve CCX per inverse.

The full six-inverse chart template achieves local Q889→888 for +72 CCX,
or Q889→883 for +180 CCX. Scalar identities and native value/phase checks
pass, and the replacement was bound to actual decoder bytes. However,
unrelated carry24+flag1+product24 regions still reach the original global
peak. The emitted full intermediate remains Q889 and adds180 Toffoli.
It increases cost and is **not included in the submission**.

The charged DQI cost is R * Q^2 * mean_Toffoli. A local reduction of six
helpers has no score value until every larger whole-program peak is lowered.
The reset/branch lifetime audit is conservative; its peak is not a lower
bound on what all possible circuit rewrites could achieve.

Files: `score5_dqi_width_report.md`, `score5_dqi_width_manifest.json`,
`score5_chem_width_review.md`, `score5_chem_width_late_classification.md`.

## Remaining accuracy limitation

The integrated projective norm repair handles the denominator-zero class
identified in the earlier decoder. A distinct numerator-zero class remains.
The implemented general two-pivot repair of that node changes the polynomial
view used by 41 later residue interfaces. Its propagation costs at least1968
additional Toffoli before other overheads. This is not a cheap isolated
48-gate whole-decoder repair. No accuracy or score benefit is claimed for it.

Files: `score5_dqi_failure_report.md`,
`score5_dqi_guard_generic_width.md`. The final report distinguishes finite
default verification from known regressions and from universal correctness.
