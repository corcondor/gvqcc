# Exact rank-11 SAT model for shared GF(8) multiplication

## Result and scope

The symmetry-normalized rank-11 problem completed with **UNSAT in two independently written encodings** using Z3 4.15.4. The BitVec encoding took 9.32 seconds; the Boolean/XOR encoding with an independent polynomial oracle took 12.26 seconds. Both used about 59 MiB maximum resident memory. Both exact SMT2 instances are saved. No rank-11 decomposition or new circuit was produced; the accepted e4 artifact is unchanged.

The reduction to this finite problem was checked independently by `score6_dqi_shared11_independent.py`. Together, the finite reductions and the two completed solver runs corroborate that the simultaneous bilinear map has rank 12. A separately checked DRAT/LRAT proof or proof-assistant certificate is **not** included. Both encodings use the same Z3 release, so this is independent encoding corroboration, not independent solver corroboration. This is not a bound on general nonlinear Boolean circuits, measurement-aware circuits, or arbitrary GF(4096) multiplication. In particular, it does not exclude a 77-term decomposition of the entire shared GF(4096) tensor; it excludes the proposed route that obtains 77 by substituting seven rank-11 shared-GF(8) subkernels.

This search is distinct from the previous Polytof walks: it specifies the exact rank-11 equations with a complete necessary first-factor classification, rather than a neighborhood of the old rank-12 decomposition.

## Tensor and coefficients

The function is

\[
(a,b,c)\longmapsto (ab,ac),\qquad a,b,c\in\mathbb F_8.
\]

The tensor dimensions over \(\mathbb F_2\) are \(3\times6\times6\). The pinned source is `symmetry_dqi_20261115_gf8_joint12_input.txt`, SHA256 `8446959c7d46f19571ce207d024f302cf28792bc04d1a5a6e7d5e3abc0913077`. It supplies 12 rank-one terms. For the three input slices, the SAT constraints are exactly

\[
M_j=\sum_{i=1}^{11}u_{ij}\,w_i v_i^{\mathsf T},\qquad j=0,1,2.
\]

All 108 Boolean coefficients are constrained. Each unknown \(v_i,w_i\) is a nonzero six-bit vector. There is no reachable-input approximation and no numerical tolerance.

## Why only one first-factor pattern is required

Let \(h(a)\) count terms with \(u_i\cdot a=1\). Every nonzero input \(a\) gives an invertible six-dimensional multiplication map, so \(h(a)\ge6\). Each nonzero three-bit covector is active at exactly four of the seven nonzero inputs. Thus

\[
4r=\sum_{a\ne0}h(a)\ge42,
\]

which excludes \(r\le10\).

For \(r=11\), the total is 44. The only possible excess-weight patterns are one weight 8 and six weights 6, or two weights 7 and five weights 6. If \(m_u\) is the multiplicity of first factor \(u\), inverse Walsh transformation gives

\[
m_u=-\frac14\sum_{a\ne0}(-1)^{u\cdot a}h(a).
\]

The two-weight-7 case makes some multiplicities half-integral and is impossible. For the one-weight-8 case, with distinguished point \(a_0\),

\[
m_u=1+[u\cdot a_0=1].
\]

The independent checker enumerates all 12,376 nonnegative seven-part compositions of 11 and finds exactly these seven patterns. Scalar field autotopy sends the distinguished point to coordinate 1; it is verified on all 3,584 scalar/input combinations. Therefore it suffices to fix

```
u = [1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 7].
```

Within a repeated-u group, the v factors are sorted strictly. Equal v factors would combine their w factors and yield at most 10 terms, contradicting the bound above.

## Additional exact reductions

The centralizer of simultaneous scalar multiplication is GL(2,GF(8)). The independent checker constructs all 3,528 group elements and verifies the action on all 63 nonzero v vectors. This permits fixing the unique u=2 term, index 2, to v=1.

The stabilizer of v=1 has 56 elements and moves v=8 through exactly the 56 vectors outside the first three-dimensional field line. At slice a=2, the six active v factors form a binary basis. Hence at least one of its other five factors lies outside that field line. The additional symmetry constraint is therefore

```
v[3] == 8 OR v[4] == 8 OR v[8] == 8 OR v[9] == 8 OR v[10] == 8.
```

This remains invariant under within-group permutations.

For each of the six non-distinguished slices, exactly six terms sum to an invertible matrix. Writing that matrix as W V-transpose shows both sets of six factors must be bases. The optimized SAT model includes every distinct nonempty subset-XOR inequality for those factors, giving 612 redundant constraints across the v and w axes. These are necessary conditions already implied by the tensor equations, exposed to accelerate the solver.

## Recorded runs

| Instance | Limit | Result | Time | Memory evidence |
|---|---:|---|---:|---|
| First-factor pattern and duplicate ordering; proof objects enabled | 300 s | UNKNOWN: timeout | 302.80 s | Z3 internal maximum 2,151 MiB; resident peak not recorded |
| Full normalization and basis cuts; proof objects enabled | 60 s, configured 768 MiB | UNKNOWN: out of memory | 18.15 s | Resident peak 546 MiB |
| **Identical normalized SMT2**, proof objects disabled | 42 s, configured 768 MiB | **UNSAT** | **9.32 s** | **Resident peak 59 MiB** |
| **Independent Boolean/XOR equations and polynomial oracle** | 60 s, configured 768 MiB | **UNSAT** | **12.26 s** | **Resident peak 59 MiB** |

The proof-enabled and proof-disabled normalized BitVec SMT2 files have the same SHA256:
`32503b39cba089014333c5eaa24dd3ccdd3d3f814bcbdd015310a6c3a63bfda1`.
The change only disabled proof-object retention and allowed Z3's efficient SAT pipeline. The timeouts and memory exit are not themselves treated as lower bounds. The independent Boolean encoding has SHA256 `e64d6c613be39db376c60ed7cfbb1af0b033ed3a3e044859ae4e3518b89aa648`. Its constants are generated directly by binary polynomial multiplication modulo x^3+x+1 (0xB), and that oracle is matched to the supplied tensor on all 512 input pairs. It imports neither the BitVec coefficient generator nor its SAT model. No further synthesis search was started.

## Reproduction

Use Python with `z3-solver==4.15.4.0` installed. If the pinned local solver directory is absent, the scripts import the installed z3 package normally.

```bash
python score6_dqi_shared11_independent.py
python score6_dqi_shared11_sat_noproof.py --out score6_dqi_shared11_sat_noproof.json --timeout-seconds 42 --fix-first-v
python score6_dqi_shared11_boolean.py --out score6_dqi_shared11_boolean.json --timeout-seconds 60
```

The original and proof-enabled normalized experiments are also preserved as `score6_dqi_shared11_sat.py` and `score6_dqi_shared11_sat_basis.py`. Their JSON receipts record the actual timeout or memory outcome; they are not successful proofs.

The solver would verify all 108 coefficients and all 512 possible (a,(b,c)) input pairs before accepting a SAT decomposition. Since the completed result was UNSAT, no circuit emitter, quantum phase claim, whole-decoder verification, or score improvement follows from this experiment.
