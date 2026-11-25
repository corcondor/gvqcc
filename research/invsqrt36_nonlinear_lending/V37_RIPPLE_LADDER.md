# V37 — shared reversible carry ladder and multi-row integration
Research only / NOT SUBMISSION. Parent PR86 native SHA d873f84acb4a9afb5652f7f56597728953beb60d91afdb7262a6a4249e9f8274. PR90 is the research branch base. Not a comparison against PR94's different native parent.

## Verified serialized results
| variant | ops | E | all-37 occupancy cuts |
|---|---:|---:|---:|
| parent | 51024 | 1442.3125 | 3702 |
| 6-exchange/bridge | 51055 | 1454.3125 | 3671 |
| 13 arithmetic cells (11 exchanges) | 50967 | 1454.3125 | 3656 |
| 130 distinct exchanges, wide | 50826 | 1573.3125 | 3299 |
| budget +9 E | 50997 | 1451.3125 | 3665 |

All independently re-read native KMB and exact replay on 3,133,452 inputs and 1,281 independent source HMR variables; source events aligned by measurement record within each group. Exact data, phase, rotation observations, scopes, guard and classical state equality. Whole circuits remain 37Q. No official score / verifier result. No main/Kaggle changes.

- New reverse-measured chart: in-place v=ab xor c, HMR(a), reconstruct u=v xor ((not b)*a); add m*u to get source phase m*c. Exact new local replacements 7087,7474; 7087 direct-output fit improves +3 to +1 E and is included in budget.
- Delayed clean product bridge 7523: affine transported factors (q17 xor q26 xor q27)(q20 xor q21), borrowed q26 compute/use/uncompute, HMR520 retimed to clean q35 after HMR521, matching original CZ cancels measurement sign. Exact as part of integrated group.
- MAJ/UMA shared reversible ladder, adapted from Cuccaro et al. https://arxiv.org/abs/quant-ph/0410184 . Store successive carries in distinct operand lines; pre-sample original HMR records on a verified clean q35; forward phase on actual incoming carry; reverse UMA restores operand/sum; first original HMR performed on restored initial carrier. Original phase and affine side effects retained, some deferred until reverse sweep. Last dirty carry target or terminal carry use integrated. Python exhaustive truth tests 174760 bit inputs across lengths 1..8 (sum of 2^(2n+1)); the full native check is independent BDD, not a Lean proof of reachability.
- Two rows / 13 arithmetic cells (11 q36 exchange motifs), source [7402,7689), 287 -> 230 commands, +12 E, q36 unused. Fragment SHA 1c1c90e7a25b0b9f19d9ec4c5615f2fdaa1180790576a9fe0afb5440af26a1f7. Integrated SHA 273afe313c0faf553148e235350e6992716898316c265aac193ddbfb936d7.
- 19 consecutive rows, 119 distinct exchange motifs (not 119 cells in a single unbroken carry ladder), physically q36-free source [7943,10000), 2057 -> 1916 ops, 159 -> 278 paid, 139 HMR. Fragment SHA 9e7ea1378d38d54274b79cebe2344266ebe587af4c891e61105a8d81bc47a1a2. Combined with first two rows = 130/161 distinct source motifs. Integrated SHA dbd8253a03b55c512a797de34aea34153257c48b0d33754c54d2fe987812c3ab. 403 fewer occupancy cuts. Paid overhead +131; not a competitive cost variant.
- Budget: 7087, [7402,7598), 9368. E=23221/16 (same as PR90 budget), 50997 ops, 3665 cuts (10 fewer than PR90 width-budget). Source span 196 -> 163 commands; +7 E. Integrated SHA 5e5cdd616bf5520a4dcab2afbbacfd71f44de1a58697097793191783a495e3bc.
- Alternative cubic cofactor screen: 27 motifs × 3 charts, 34 sampled fits (17 distinct motifs), no full replay of these polynomials; transported prefix constructed through 6 stages, cost rises 19,41,75,127,191 paid on individual later stages, rejected on cost. Direct output quadratic chart: 414 queries, two sampled fits, 7087 direct verified. 307 generated CCX screened for affine increment or affine reset, zero candidates. One 6-exchange row (7759...) not lifted due nonstandard terminal q36 product; rest of original motifs outside these rows not solved by this integration.
- Khattar/Gidney conditionally clean ancillae https://doi.org/10.22331/q-2025-05-21-1752 informs borrowed-hub alternatives; Cuccaro ladder is the actually implemented basis. Lean 4.35.0 CI configured, generic Boolean identities and list induction, not full circuit formal proof.
- Full source, native parents, outputs, replay receipts, exact group indices, failed screens and reproduce commands in conversation companion archive. No main merge or official score claim.
