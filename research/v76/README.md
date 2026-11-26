# V76 coupled nonlinear state and phase transport — research, not submission

Issue #163 acceptance is unchanged: full physical circuits, width and paid cost improvement, and correct verification. This branch is **not a score improvement**.

## Unified law

Work in the Boolean function algebra restricted to the reachable input/history domain D, not merely an affine vector space. For an omitted state v and physical carrier w, let v=f0(z)+w f1(z). Pull a measurement's outcome-dependent correction through the following affine segment to express w=g0(z)+v g1(z), if that equality is proved on D. Then w+v=f0(z)+(1+f1(z))(g0(z)+f0(z)g1(z)). The carrier can be updated by this difference, and the measurement phase is transported into the new chart. Both identities must be certified; a measurement is not simply a deletion. The discrete product rule supplies the quadratic cross term. JointExchange.lean contains the local proof source (Lean build not run). joint_exchange.py implements exact quadratic-span search over the full live carrier basis.

## Experiments actually run

- Chemistry: the 211-CCX banks 8, 13, 14 have a 99-dimensional invariant cache (including constant), 129 independent nonlinear generator directions modulo the cache, and a 7-dimensional intersection of cache and output-difference spaces. Search 1,243 first factors against the full 99-dimensional partner space, then 618 first factors against the paired 129-dimensional carrier space (cache plus 30 output bits). No admissible 3-to-2 replacement. All tested banks remain 211 CCX. Not an exhaustive exclusion of other generators. V74 full-family parent remains unchanged.
- DQI: parent V74 SHA256 650dba6bc07582a0bc70860d9a2608b75dfe7cb15586efae4f0459c77d77e52. Dual pullback through 11 conditional correction gates at source HMR index 20140284. Independent truth-table replay from cut 20135562 on 22 unconstrained input coordinates and eight zero scratch coordinates: 4,194,304 rows, 2,063,872 nonzero residual rows. Residual ANF degree 8, 10,056 monomials. This overapproximation refutes using the unrestricted local chart as a certificate; it does NOT establish an error of the source on reachable inputs. Exact joint quadratic difference fit in 30 carrier coordinates has rank 466 and 441 remaining ANF terms. Earlier rebase also fails before the HMR. No valid 899Q circuit emitted. Full C++ implementation and raw logs are in the V76 companion research archive.
- Chemistry resource formula from verifier: Q_total = Q_persistent + max(Q_temporary,heuristic, Q_temporary,loader). Shrinking existing scratch below the heuristic peak does not change total cost at unchanged batch size and factorization.
- Invsqrt: no new complete candidate in this experiment. No new 37Q invsqrt/900Q DQI candidate.
- No official verification, Lean build, or Kaggle submission. No claims of full circuit success.

Prior results: #20, #68, #92, #132, #134, #155, #158, #159, #160, #161, #162, #163. The formula is a necessary local rewrite law, not a proof of cross-circuit composition.
