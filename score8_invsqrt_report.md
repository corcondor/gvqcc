# score8 invsqrt: approximate phase fitting and complete cleanup resynthesis

## Outcome

**No new invsqrt candidate is accepted.** The Q46 incumbent remains
`684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`, with official
mean Toffoli count 1,478.7506100300882 and cost 78,673.55534364567. Its existing
200,540,928-shot PASS receipt is `score3_invsqrt_full_verification.json`.
No new benchmark KMB, official full rerun, or Kaggle submission was produced.
No optimization process remains running from this branch.

This batch did not restrict the candidate objective to XOR/AND counts. It
searched changes to generic `Z_POW` phases and to complete conditional phase
corrections, including free `Z`/`CZ` and native paid `CCZ`. It did not complete
a new arithmetic architecture or Q45 implementation.

## 1. Approximation-aware Clifford/T lattice test

The existing score6 certificate covers exact reweightings of 38 unchanged
phase predicates. This batch extended it to **approximate** reweightings.
Let A contain 40 witness evaluations and let the published integer matrix B
satisfy BA=I. If both incumbent and candidate pass the phase tolerance, their
coefficient change modulo an integer is bounded, component by component, by

`abs(delta_j mod 1) <= sum_i abs(B_ji) * 2 * tolerance(x_i)`.

The bound allows a constant phase. All arithmetic in this exclusion step is
integer/rational, using the official integer tolerance formula. A separate
checker recomputed BA=I and every bound.

- **19 of 33 generic rotations** cannot reach the nearest Clifford/T lattice
  point (a multiple of 1/8 turn) under that bound.
- The remaining **14** were individually forced to that lattice point and
  the other generic coefficients were minimax refit on all 3,133,452 inputs.
- Only the known small q30 phase could be removed with positive margin:
  2.7083574994e-13 turns. Its predicted cost rises to **79,277.84284** because
  the synthesis precision becomes more expensive.
- The other 13 forced removals have negative final margin.

The full-domain LP batch took 36.52 seconds. These fits use long-double
baseline phases and float64 linear programming; they are numerical search
results, not exact native acceptance proofs. All failed candidates were
rejected before emission. The five originally Clifford/T coefficients remain
fixed in these LPs. Changing the phase features or arithmetic is outside this
fixed-feature result.

Receipts: `score8_invsqrt_sparse_phase_result.json`,
`score8_invsqrt_sparse_phase_audit.json`.

## 2. Measurement-aware whole-phase rewriting

The target of these searches is a complete phase polynomial, rather than an
individual AND gate. Internal measurement outcomes are symbolic, their phase
coefficients must cancel, and an eliminated outcome must be dead outside the
removed cleanup. Conditional data blocks must restore their input values.

| New search | Scope | Result |
|---|---|---|
| Whole conditional block to arbitrary Z/CZ | 53 paid blocks; 4,442 legal inputs | No quadratic phase model |
| Complete measurement correction immediately after HMR | 50 paid cleanup lifetimes; 4,443 legal inputs | No quadratic phase model |
| Relocate complete correction to another time | 50 lifetimes, 1,186 nonlinear boundaries, 19,859 queries; 2,247 legal inputs | No model |
| Whole costly block to one CCZ plus arbitrary Z/CZ | 10 blocks; raw-wire pair times arbitrary live parity, plus arbitrary quadratic phase; 4,224 legal inputs | No model |

The relocation search permits any retained live wire in a quadratic phase
expression, and searches after the original measurement until its classical
bit is overwritten. It excludes conditional-data routing and arbitrary
nonlinear encodings. The one-CCZ search does not allow arbitrary parities in
both of the first two factors. A negative linear system on a legal input
subset excludes the stated identity on the full domain; it is not a global
circuit lower bound. No candidate from these searches required a full-domain
positive verification.

## 3. New phase predicates across the full arithmetic tape

The older structural phase search sampled three snapshots. This batch
collected **7,621 distinct intermediate wire values across the full tape**.
Minimax LP dual weights selected features that distinguish the tight phase
constraints. A second version solved for arbitrary affine parities of live
wires at 511 cuts. Such a parity can be computed in a participating wire,
phase-rotated, and restored using only CX/X, without extra qubits or Toffolis.

Three objectives were tested: add one phase; remove one small phase and add
one; remove two small phases and add one. The last two hold generic rotation
counts at 33 and 32 respectively. Existing generic coefficients were refit
within +/-1e-5 turns; the named removed coefficients were fixed to zero.

| Feature family | Add one | Replace one | Replace two with one |
|---|---:|---:|---:|
| Actual intermediate wire values | 600 coarse LPs | 1,000 coarse LPs | 1,000 coarse LPs |
| Dual-guided arbitrary affine parities | 1,600 coarse LPs | 600 coarse LPs | 1,394 coarse LPs |

This is **6,194 coarse LP screens**, not 6,194 full-domain accepted circuits.
Each coarse LP uses legal input constraints and gives a numerical upper bound
for the same bounded fit. The five shortlisted fits were separated on the
complete legal domain. None improved cost. The best genuinely new
replacement feature produced margin 2.2543449102e-12 turns and cost
78,988.92669. Two features merely reproduced the existing small phase; their
floating estimate differed by about 0.0000067 cost. They are recorded as
numerical ties and **not counted as gains**. Changes below 0.001 predicted
cost are not promoted without stronger evidence.

The searches are bounded subsets ranked by dual weights and weighted residual
projection. They do not exhaust arbitrary Boolean phase functions, every
affine parity at every cut, or alternative arithmetic circuits. Compact
receipts omit unused coarse-fit coefficient vectors and retain all full-fit
coefficients.

## 4. Why reaching 28 needs more than phase-only refinement here

The following is a scoped mathematical bound, not a universal quantum-circuit
bound. Fix one measurement transcript of a **monomial basis-state circuit**:
each generic rotation contributes an angle times a Boolean predicate, and
Clifford/T phases contribute multiples of 1/8 turn.

For x=65,...,3,133,452 all allowed output phase intervals lie strictly within
(0,1/8) turns. They are pairwise disjoint. Both facts are checked by exact
rational inequalities in `score8_invsqrt_phase_lower_bound.py`.
There are 3,133,388 such intervals, more than 2^21. For a fixed pattern of k
generic predicates, Clifford/T choices can supply at most one phase in that
interval, because their alternatives differ by 1/8 turn. Therefore **k >= 22**.

Now additionally hold **Q46 and the incumbent arithmetic mean fixed**, and
apply the verifier's equal-error rotation synthesis tariff. Even granting
22 generic rotations, zero approximation error, and no T-class charge gives
an ideal cost lower bound of **74,690.25549**. The maximum phase-only reduction
under those assumptions is 5.0631%. Reaching portfolio score 28 by changing
only this component would require cost at most **73,117.83872**. Thus this
phase-only family cannot deliver the whole required improvement by itself.
Arithmetic changes, width changes, other permitted circuit models, and
improvements in other components are not ruled out.

## Reproduction

Run from the repository directory. `PY` below denotes a Python with NumPy and
SciPy. The existing `invsqrt_structural_work/basis.{json,u64}` is a reproducible
truth-table intermediate pinned by this batch's manifest. If missing, run the
existing `invsqrt_structural_extract.py` from the repository's parent directory
to regenerate it from the pinned e46 source. The incumbent score3 arithmetic
rewrite preserves those phase predicates.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_sparse_phase.py --out /tmp/score8_sparse
"$PY" score8_invsqrt_audit.py --out /tmp/score8_sparse_audit.json
"$PY" score8_invsqrt_phase_quadratic.py --out /tmp/score8_phase_quadratic
"$PY" score8_invsqrt_cleanup_clifford.py --out /tmp/score8_cleanup_clifford
"$PY" score8_invsqrt_cleanup_relocate.py --out /tmp/score8_cleanup_relocate
"$PY" score8_invsqrt_phase_oneccz.py --out /tmp/score8_phase_oneccz
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_global_feature.py --out /tmp/score8_feature_add --limit 600 --full-limit 30
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_global_feature.py --out /tmp/score8_feature_drop1 --drop 16 --limit 1000 --full-limit 30
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_global_feature.py --out /tmp/score8_feature_drop2 --drop 16 19 --limit 1000 --full-limit 30
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_global_parity.py --out /tmp/score8_parity_add --limit 1600 --full-limit 40
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_global_parity.py --out /tmp/score8_parity_drop1 --drop 16 --limit 600 --full-limit 30
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$PY" score8_invsqrt_global_parity.py --out /tmp/score8_parity_drop2 --drop 16 19 --limit 1600 --full-limit 40
python score8_invsqrt_phase_lower_bound.py --out /tmp/score8_phase_lower_bound.json
```

Only `score8_invsqrt_*` files were added. The baseline, older receipts, and
official verifier were left unchanged. `score8_invsqrt_manifest.json` binds
this source, compact receipts, and read-only dependencies.
