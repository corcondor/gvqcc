# Mixed Schur pivot: replace the redundant source word

A direct mixed pivot has an algebraically valid inverse with one reciprocal,
but naively retaining the two source evaluations is not reversible.
The new four-word record restores the entire polynomial pair, with no extra
word compared with the naïve record. This is a reference for a local repair,
not a candidate full circuit and not a result on archived raw-S inputs.

Write (G=(A,B)), (g_0=G(t)), (g_1=G(s)), (\Delta=t+s\ne0) and
(c=\det(g_0,g_1)/\Delta\ne0). The relevant pivot matrix is
(igl(\begin{smallmatrix}0&c\\c&d\end{smallmatrix}\bigr)).
Let (
ho=d/c), and let (R) be the polynomial pair after the direct
Schur update and division by ((X+t)(X+s)). Express (G=\lambda g_0+\mu g_1)
and (R=\lambda' g_0+\mu' g_1), where primes label the reduced coordinates
rather than derivatives. Expanding the cross products gives
[
 \mu=(X+t)^2\mu', \qquad
 \lambda=(X+s)^2\lambda'+\Delta\rho(X+s)\mu'.
]
In particular (\mu(s)=1), so (\mu'(s)=\Delta^{-2}). The replacement for
the four original evaluation coordinates is
[
 (g_{0,A},g_{0,B},\rho,\tau),
 \qquad \tau=(\Delta/c)\det(g_1,R(s)).
]
Use the same reciprocal of (c) for both (\rho) and (\tau).
The reverse recovers (g_1=\Delta^2R(s)+\tau g_0). Then
(\mu'=\det(g_0,R)/\det(g_0,g_1)) and
[
 G=(X+s)^2R+\Delta^2\mu'g_1+\Delta\rho(X+s)\mu'g_0.
]
The inverse needs one shared variable reciprocal of the recovered determinant
for this reconstruction, plus field products; it is not free. After it
reconstructs the pair, the cross block and (d) can be evaluated again. If
the two pivot RHS words are retained, their two-value Schur update is inverted
without a separate copy of either RHS polynomial.

## Limits and test evidence

The replayed collision has 4,096 inputs that produce one naïve record,
whereas the replacement record separates all 4,096 and restores every one.
The collision family uses arbitrary coprime coefficient pairs. The additional
synthetic squarefree locator cases exercise the formula at discovered mixed
pivots; this does not establish their reachability at any specific frozen
raw-S decoder boundary or the cost of selecting those points coherently.

The native test emits **only** the reversible g1 reconstruction on six
physical words with the public node separation fixed, provided (R(s))
is already on two words. Using the existing rank-42 multiplier, it keeps the
CCX/paid count at 84 and reduces instructions from 1,020 to 870 at
(\Delta=1), or 1,190 to 1,040 at (\Delta=1017) in the forward direction.
All eight serialized KickMix variants passed 1,024 lanes each, including
reverse, arbitrary spectator data, phase and executed paid gate count.
No scratch beyond those prescribed inputs/outputs and no standalone T gates.
The four local ring lemmas passed strict Lean 4.35.0. They do not prove
general coherent pivot routing or the native full decoder.

Do not count the coupon as a net saving versus the two-scalar fallback.
One must still place the packed words, reversibly replace the two live
source evaluations, compute and uncompute the selected evaluation and
denominator inverse, and compare the **total** round-trip charge with that
fallback on the actual #257/#279 seam. No full-tape modification,
Kaggle submission, merge or score.

## Reproduce

Use the #261 helper modules (crt882, joint_phase and dependencies) at
bf87158c58b5f183f08798d6d449e42c10177019 on PYTHONPATH, KickMix 1.0.0,
and NumPy, then run mixed_pack.py, mixed_row_native.py, and
lean -DwarningAsError=true MixedPacking.lean.

### Native retirement once the witness is available

After the forward witness is valid, erase obsolete (g_1) using HMR and
the exact phase debt
[
 m\cdot g_1=m\cdot(\Delta^2R(s))+m\cdot(\tau g_0).
]
The linear part is Clifford; the bilinear part is a classical-mask
controlled phase. On the same 96Q interface and for both public separations,
the native charged cleanup falls from **84 CCX/paid to zero**. Production
records are cleared. Instruction counts fall 894→492 and 1,062→660.
Both production tapes pass 1,024/1,024 valid lanes. Retaining the HMR record
in diagnostics confirms the exact residual phase (m\cdot fault) in
256 intentionally invalid lanes per separation; uncompensated HMR already
flips 514/1,024 and 488/1,024 valid lanes. A fifth local Lean statement
checks the conditional repayment and its fault residual. This eliminates
explicit row erasure, not reconstructing old (g_1) during inverse.
It also does not establish that two separate temporary R(s) words can
coexist with the complete coherent pivot in 900Q.

### Strict #286 Lean repair

The adjacent anchor_strict.patch applies to the exact #286 commit
36510db98c2ddf74e411cefabb5727382906f08d. It narrows imports, replaces deprecated
push_neg, changes unnecessary simpa to direct contradiction simplification,
and gives the conditional theorem an explicit DecidableEq binder.
The patched AnchorPivot file passed Lean 4.35.0 with warnings as errors
and nine printed axiom audits. This is a verified patch file, not a write
to #286's branch. Reproduce in that pinned checkout:
```sh
git apply /path/to/anchor_strict.patch
cd research/dqi_cutoff18_strict
lake exe cache get Mathlib.Tactic.Ring Mathlib.Tactic.Push Mathlib.Algebra.BigOperators.Group.Finset.Basic Mathlib.Algebra.Field.Basic
lake env lean -DwarningAsError=true AnchorPivot.lean
```
