# invsqrt charged-operation reduction

All searches used the invsqrt member of the 27.327844992124593 portfolio. Its KMB SHA-256 is `684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`. The existing unchanged verifier result is 78,673.55534364567 at 46 qubits over 200,540,928 shots. No new invsqrt member passed the search filters.

## Dense affine factors

For a circuit cut, treat each affine-independent live wire as a vertex. The mod-2 coefficient of each cross term is an edge. The desired predicate determines a space of equivalent quadratic forms by Gaussian elimination of actual live wire values over legal inputs. A form with one AND and an arbitrary affine remainder has alternating rank at most two. Its edges are the complete tripartite graph induced by three nonzero two-bit labels, with zero-label vertices isolated. A nonzero pivot edge determines the entire candidate graph from the rows incident to its endpoints.

The search projects the quadratic nullspace onto those incident edges. Its exact enumeration is independent of factor density. Two high-rank projections were passed to a SAT solver that tests the complete tripartite construction with all quotient equations.

| Search | Outside quadratic span | Rank-two excluded | Unknown |
| --- | ---: | ---: | ---: |
| Four phase predicates at 8,245 eligible placements | 8,221 | 24 | 0 |
| Four complement predicates at 8,245 eligible placements | 8,221 | 24 | 0 |
| Six coherent 2→1 arithmetic windows | 0 | 4 | 2 |

The complement uses (f-g=f\oplus g) for (g\leq f). The search includes the four local phase windows and alternate depth-zero insertion cuts with existing clean scratch. Conditions and measurement outcomes follow the previously verified branch-restoring computational trace. The phase test used 10,985 distinct legal inputs. Since the equations represent necessary constraints on legal rows, negative results hold for the stated synthesis class over the full domain. The two arithmetic timeouts are not exclusions. An independent SAT implementation and the projected exact enumerator agreed on 200 random small cosets.

The two-step variant screened eight candidate 3→2 or 4→2 windows when the retained affine basis is preserved. Five windows had unresolved high-dimensional projections and three had no match within that family.

## Carrying a cached product into a conditional branch

Sampled matching identified 132 producer→consumer pairs at most 1,600 instructions apart. The consumer was a Toffoli in a measurement correction. For 87 pairs, unconditional measurement of a held product at the end of the correction could have been compensated by a quadratic Clifford phase. None could carry the product from its available logical value to the correction through idle registers with direct affine recovery at both ends and every handoff. Several repeated add-chain instances have cuts at affine rank 47 including the constant, immediately after a short-live product is reset. The affine routing model has no extra independent coordinate there.

This experiment tests register borrowing with affine recovery and conditional-block references as atomic barriers. It leaves nonlinear re-encoding and other scheduling changes open. No new KMB was emitted. The legacy official receipt applies only to the baseline.

## Reproduce

```sh
python highest_inv_next/quadratic_phase.py --source invsqrt_new/rebuilt_source.kmb --range whole --sat-ms 10000 --output highest_inv_next/whole_sat.json
python highest_inv_next/quadratic_phase.py --source invsqrt_new/rebuilt_source.kmb --range whole --sat-ms 10000 --complements --output highest_inv_next/whole_complement.json
python highest_inv_next/quadratic_windows.py --source invsqrt_new/rebuilt_source.kmb --windows quick_inv_score/window_rank.json --out highest_inv_next/windows_sat.json --sat-ms 12000
python highest_inv_next/quadratic_two.py --source invsqrt_new/rebuilt_source.kmb --windows quick_inv_score/window_rank.json --out highest_inv_next/two.json
python highest_inv_next/affine_cache.py --source invsqrt_new/rebuilt_source.kmb --out highest_inv_next/cache_affine.json
```

Python dependencies are NumPy and Kickmix. The optional SAT checks also require z3-solver. Window inputs reuse the previously recorded observable-free window search.
