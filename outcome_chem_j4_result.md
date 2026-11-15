# Exact-word J=4 synthesis experiment

The newly built family is correct under the tested and formally checked contract, but **does not improve the score**. Do not submit this prototype.

Source factorization: `dqi_inputs/chemistry_4033/submission_asterios_full.npz`, SHA-256 `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`. The newer public4030 factorization was not locally available. Original factorization bytes and all1220×75 integer angle words were preserved.

| Quantity | J=4 prototype | Publicv27 comparison |
|---|---:|---:|
| Number of ANGLE circuits | 19 | 15 |
| Maximum circuit qubits | 125 | ≤128 |
| Loader CCX per pass | 5434 | 4030 |
| Total Toffoli | 17530 | 14722 |
| Total task qubits | 419 | 427 |
| QT ratio at equal lambda | 1.168426 | 1 |

The J=4 target was ≤4170 loader CCX. This construction misses it by1264 and is16.84% more expensive in QT at equal lambda. The smaller task Q does not compensate for recomputing nonlinear terms in19batches.

## Construction and verification

`outcome_chem_j4_synthesize.py` actually synthesizes the replacement family. It uses69high-address monomials,11low-address monomials and2temporary control forms:82scratch plus43selection/output qubits. It applies the identity

`(A XOR H2) AND (B XOR H1) XOR (A AND B) XOR (H1 AND H2) = (A AND H1) XOR (B AND H2)`.

Here A/B depend only on the four low address bits, while H1/H2 depend only on the seven high bits. Products within one partition can be reconstructed by CNOTs from that partition's complete Boolean basis. This pairs two cross terms into oneCCX. Basis ancillas are cleaned by HMR and conditionedCZ.

Every generated circuit was proved on1232addresses with32arbitrary symbolic target bits, including exact cancellation of everyHMR phase coefficient, selection preservation and zero workspace. The extra12addresses are a native extension recovered from the old family; all1220required addresses agree with the original NPZ. Official `recover_words_from_circuits` also passed all1220addresses in both directions with1shot/address. Generation plus these checks took4.31seconds. No full numeric verifier, default-shot run or submission was performed.

The independent J=5 cost screen uses the same pairing and the known top-bit/XOR-five output transformations. It still requires4950CCX/pass, or an optimistic4875after accounting for five borrowed coded tags, above4033. No J=5 candidate was emitted.

Files: builder `outcome_chem_j4_synthesize.py`; J=5 screen `outcome_chem_j4_j5_cost_screen.json`; local prototype and proof receipts `outcome_chem_j4_paired_family/result.json`. This is a measured failure of this decomposition, not a lower bound on J=4 synthesis or proof of optimality of the original circuits.
