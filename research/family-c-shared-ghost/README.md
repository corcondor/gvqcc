# Shared two-slot inverse-carry policy — isolated MAIN research only

Integrated donor #184 (36Q, 449.5 paid, virtual quotient bits 22–25)
with the two-slot adaptive inverse of the prior #185 experiment.
The new schedule shares measured guards rather than expanding paths.

## Exact policy count
There are 7 unconditional paid steps and the subsequent terms
1[gA]+1[gB]+2[m5]+1[m4&&!m5]+1[m5&&mr], where
gA=m2||m3||m4||m5 and gB=m3||m4||m5.
Uniform independent X-measurement bits give 330/32=10.3125 expected
paid per replaced inverse row versus donor 11. Sixteen rows save 11.
Two-slot occupancy and the 512 combinations of abstract carry/debt
values are addressed in SharedGhost.lean; [Lean CI run 46009422859](https://github.com/corcondor/gvqcc/actions/runs/46009422859) succeeded on commit 4cb74e7f16124bd3d247de8001c6d17ae5673259. All eight local theorems passed; seven are axiom-free, expected_numerator depends only on propext. No sorryAx or Lean.ofReduceBool. This is not whole-circuit refinement.

## Locally executed full isolated-MAIN KMB
All 3,133,452 arithmetic HO reference inputs:
- donor main36_d reserialized: 36Q, 454 static paid, 449.49984043157514
  mean paid, 4928 serialized ops, SHA256 fb1c535db7301b019d1c4320ba100b932166a0ef89cc2b28bf9c0e55ff080e61.
- compact shared policy, merged guard and commuting cancellation:
  36Q, 486 static paid, 438.49886451108875 mean paid, 5779 serialized ops
  (1678 forward), SHA256 c12d000b33d0e9f760eb7326c61f9539060337851da59a18031a43d0be55cba3.
- donor with the same commuting cancellation: 3506 serialized ops,
  449.49984043157514 mean paid, SHA256 6441fd7b2b07ca365a131ca3135515db19ff5a7767a5705d9dd4a4b5460c2ef9.
- KickMix 1.0.0: all value, restoration, zero workspace and phase
  checks pass for the above. C++ independent KMX parser also passes
  all 3,133,452 inputs under three measurement patterns (all zero,
  all one, pseudorandom); no claim of whole-circuit exhaustive histories.

Tradeoff: paid improves by 11 vs donor but static paid and op count
increase. Retain donor as a Pareto candidate. No complete physical HO/END,
no official score or native DQI repair. No main merge or Kaggle submission.
Related: #155, #183, #184, #185, #188. Literature:
Gidney 2018 doi:10.22331/q-2018-06-18-74; Luongo et al.
arXiv:2407.20167; AlphaTensor-Quantum doi:10.1038/s42256-025-01001-1.
The upstream R32 adaptive policy is reused; our contribution is compact
guard sharing, integration and verification, not discovery of its optimum.
