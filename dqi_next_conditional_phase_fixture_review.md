# Conditional phase discovery scanner: independent fixture review

## Result

The corrected scanner passed **22 small circuit fixtures**, **1,792 exact truth-table cases**, and **11,264 native KickMix shots**. No production circuit was changed. This checks the tested discovery cases, not completeness of the fingerprint search or correctness of a hypothetical circuit rewrite.

Scanner SHA256 tested:

`c9363a304277b4832f7be08e7168edbc7836d1fba995a46426b635ef9d5dfbd6`

The initial code had a concrete opcode error. The KMB opcode assignments, also recorded by the repository's format reader `kmb_profile.py`, are:

| Opcode | Operation | Guarded update |
|---|---|---|
| `0x40` | `BIT_STORE0` | `b <- b XOR (g AND b)` |
| `0x41` | `BIT_STORE1` | `b <- b XOR (g AND (b XOR 1))` |
| `0x42` | `BIT_INVERT` | `b <- b XOR g` |

The original scanner assigned these updates in a different order. The parent agent corrected those cases before the successful fixture run and repeated the production scan. The previous production run cannot independently establish its negative result.

## What was checked

Each fixture's quantum and classical inputs are enumerated independently. HMR outcomes, including outcomes on inactive conditional branches, are enumerated as independent bits for the truth tables. The oracle implements gate semantics directly from the KMX names, without using the scanner's fingerprints or KMB opcode switch.

The native checks use every assignment of four quantum input bits and two initial classical input bits, repeated four times in a batch of 256. They use seeds `202611151` and `202611152`. Quantum outputs, classical outputs and exact pi-phase parity agree with the independent oracle in every checked shot.

The fixtures cover:

- Conditional X, CX, SWAP, CSWAP and CCX, then the same operation again, causing the original CCZ phase predicate to reappear.
- The same quantum phase under different guards, which must not be presented as immediately cancellable.
- Classical bit inversion, store0, store1, and conditional updates.
- PUSH_CONDITION capturing the old predicate even when its classical source bit changes inside the scope, including nested scopes.
- New HMR outcomes overwriting guard bits, and HMR resetting one factor of a CCZ.
- Conditional HMR, and R reset of a CCZ factor.
- Zero, one, equal, complementary, and affine-rank-two factor reductions.

For every reported repeated phase, the truth tables verify equality of the **quantum phase product**. If `same_guard=true`, they additionally verify equality of the actual guard. A false `same_guard` means the fingerprints do not establish equality; it is not a proof that predicates differ.

For every reported reduction, the independent truth tables verify the claimed relation between the three factor functions. Discovery results are not automatically converted into gate removals.

## R handling

Native KickMix R on a nonzero value introduces an unrecorded random phase. The fixture oracle therefore models R's phase as an independent discarded-measurement outcome. For the native R fixture, a companion circuit replaces R with HMR into a spare classical bit, using the same simulator seed. The test first confirms exact agreement of the companion's quantum values and phase with the original R circuit, then uses the observed outcome in the independent oracle. The original circuit's classical output is still checked without introducing that outcome bit.

The scanner follows quantum values through R and HMR; it does not certify cancellation of their phase debts. Its `DISCOVERY_ONLY_REQUIRES_EXACT_REPLAY` status remains necessary.

## Limits of the fingerprints

The hash construction implements selected simplifications, XOR cancellation, commutativity of individual AND nodes, complements, and idempotence. It is not a canonical Boolean normal form. Distributivity, associativity across different expression trees, or functional identities outside those rules can be missed. A zero-opportunity scan is therefore a negative result for this scanner, not a proof of a lower bound.

The hashes are 128-bit discovery fingerprints. Independent exact replay is still required for any real positive candidate. These small fixtures do not eliminate the possibility of collisions or untested implementation errors.

## Reproduction and files

`dqi_next_conditional_phase_fixture_check.py` compiles the scanner, emits the small KMX/KMB fixtures, reruns discovery, and checks both truth tables and native simulation. It requires KickMix and NumPy. The compiled scanner is a temporary workspace artifact outside the repository.

```bash
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python dqi_next_conditional_phase_fixture_check.py
```

The full results are in `dqi_next_conditional_phase_fixture_results.json`; small circuit fixtures and discovery records are in `dqi_next_conditional_phase_fixture_data/`.
