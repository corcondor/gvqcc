# Actual-domain relation and 16-row cofactor experiments

## Outcome

**No lower-cost candidate was obtained in this bounded experiment.** The original 4033 loaders, README, scoring worker, and submitted DQI circuit were not changed. No candidate KMB was emitted, no official scoring run was started, and no external push or submission was performed.

This experiment removed the previous assumption that entry wires are independent abstract variables. The first search used the exact 1220-address domain with both actual incoming batches. A separate route used the four low address bits, the five conserved tags, and the 16-row block structure to evaluate a different joint-output decomposition.

The result is limited to the classes below. It does **not** establish that 4033 is optimal, that every small-cone rewrite is exhausted, or that the competition score cannot improve.

## Result files and provenance

| File | Role |
|---|---|
| `chemistry_relation_screen.py` | Actual-domain product-quotient and measurement-uncompute screen. |
| `chemistry_relation_screen.json` | Completed quotient/uncompute result. |
| `chemistry_relation_cofactor_rank.py` | Cofactor-matrix output-basis screen, with an optional coded-parity extension. |
| `chemistry_relation_cofactor_rank.json` | **Initial** run: 7175 output masks per circuit, using weight-one, weight-two, and weight-three output combinations. |
| `chemistry_relation_cofactor_coded.json` | **Final expanded run:** 87242 masks per circuit, including coded five-word parities. This is the final cofactor result. |
| `chemistry_relation_context_check.py` | Reproducible standalone code for the independent canonical/actual input-model check. |
| `chemistry_relation_cofactor_context_check.json` | Independent comparison of the canonical-tag model with both actual incoming batches at every extracted control wire. |

The initial and final cofactor JSON files were not overwritten. Their script hashes differ because the coded-parity option was added between runs. The current script hash matches the final expanded JSON.

## 1. Existing-product dependencies on the actual reachable domain

For each circuit, the exact previous batch and current batch were combined into one 2440-bit truth vector. Thus every proposed identity had to hold in both the forward and reverse uses of the circuit.

Let `V` be the GF(2) span of the constant and all entry **control** wire functions in an extracted output-accumulation block. This space has rank **91** on the actual domain. Mutable output-data wires are not included in `V`; this keeps the proposed free corrections available while output products are rescheduled.

The test reduced every CCX control product modulo `V`, then checked the rank of all such residual products together. This is stronger than checking whether one CCX product itself is already a live-wire XOR. It would detect an identity such as `p_i XOR p_j XOR p_k ∈ V` and permit existing products to be shared across different output directions.

| Batch set | Products per block | Quotient rank | Reduction |
|---|---:|---:|---:|
| 1, 2, 3 | 212 | 212 | 0 |
| 4, 5, 7, 9, 11 | 189 | 189 | 0 |
| 6, 8, 10 | 187 | 187 | 0 |
| 12, 13, 14 | 188 | 188 | 0 |

All **2706** extracted products are independent modulo their block's entry control-function space. Therefore no combination of the **existing products** can be eliminated by this quotient-linear sharing method. This does not exclude replacing them with different products of different functions.

**Batch 0 was not covered by this quotient test.** Its output-accumulation span crosses a nonlinear update of a control/workspace wire, so the extractor rejects that block. The result must not be described as an all-15-circuit quotient lower bound.

### Measurement-based elimination of a target update

Separately, all **4033 CCX gates across all 15 circuits** were tested for a measurement-uncompute replacement. The question was whether the **post-CCX target**, rather than the control product, is an affine function of the other current wires on both allowed incoming states.

If that identity held, the old target could be erased by HMR, its phase corrected by the original control product and the affine post-target function, and the new target restored with X/CX gates. This is a different condition from the earlier CCX-to-linear span test.

**No such target was found.** No measurement rewrite was emitted. The combined quotient and target screen took **3.407 s**, with **46.19 MiB** peak RSS.

## 2. Actual 16-row structure and conserved tags

The five preserved coded-word tags are

\[
s_j=z_{8j+6}\oplus z_{8j+7},\qquad
s^*(a)=(a_0a_1,a_0a_2,a_1a_2,a_0a_3,a_1a_3).
\]

The canonical-tag model was independently checked against the exact previous and current input batches. For each of batches 1–14, every one of the **90 entry control wires** agreed for all 1220 valid addresses in both directions: **34160 address/direction cases**. This validates the input model used below; it is not a proof of a newly generated circuit.

Each extracted CCX control separates as `h(high_address) XOR l(low_four_bits)`. The high functions differ between gates, while low functions are reused. The low-function space has rank **15**, as expected for the nonconstant Boolean functions on four bits.

### Grouping a common two-dimensional low-function space

The search grouped products whose two low factors span the same two-dimensional subspace. If the output directions within such a group were dependent, their high coefficients could be combined into fewer products before synthesis.

There were **2219 groups** across the 14 circuits; the largest group had **9 products**. Every group's output directions were independent, so this grouping gave **0 reductions**.

## 3. A different joint-output decomposition

The second synthesis route formed a cofactor matrix for every combination of output bits. There are 35 non-tag output bits; the five tag bits are retained through their proved conserved values.

For output function `f`, the cofactor matrix is

\[
M_f(h,l)=f(h,l)\oplus f(h,0)\oplus f(0,l)\oplus f(0,0).
\]

This removes functions depending only on the high or low address. A rank-`r` matrix decomposes into `r` bilinear products. Two bilinear terms can be packed into one AND using high-only and low-only correction functions, giving the core-product indicator `ceil(r/2)`.

The finite search then chose a minimum-weight linear basis of output combinations. The weight of a combination was `ceil(rank(M_f)/2)`. Greedy selection is valid for this finite weighted linear-basis problem.

**This class synthesizes the selected output functions separately and does not introduce new product sharing between those selected outputs.** That restriction is material: the existing circuit already has a more economical joint product decomposition.

### Initial and final candidate sets

The initial run considered all nonzero combinations of one, two, or three of the 35 output bits: **7175 masks per circuit**.

The final run also included the complete linear span of the seven bit-plane parities across all five words, XORed with zero, one, or two individual output bits. These are directly motivated by the known coded-word structure. After deduplication there were **87242 masks per circuit**, or **1221388 evaluated masks** across 14 circuits.

### Measured synthesis indicators

| Batch set | Existing core products | Final selected-basis indicator | Additional core products |
|---|---:|---:|---:|
| 1, 2, 3 | 212 | 280 | +68 |
| 4, 5, 7, 9, 11 | 189 | 241 | +52 |
| 6, 8, 10 | 187 | 235 | +48 |
| 12, 13, 14 | 188 | 238 | +50 |
| Total over batches 1–14 | **2706** | **3464** | **+758** |

The known coded parities do help this alternative construction: for example, its indicator falls from 250 to 241 in batch 4. But the existing batch-4 circuit uses only 189 core products. This is not an improvement over the submitted loader.

**3464 is not the Toffoli count of a completed candidate circuit.** High/low correction synthesis, possible helper generation, qubit allocation, and cleanup have not been compiled into that number. Because the core indicator already exceeds the existing cost in every batch, no candidate circuit was constructed or claimed to pass verification. The final expanded run took **17.683 s**, with **47.86 MiB** peak RSS.

### Address-domain qualification

The table has 76 complete blocks of 16 addresses and four valid addresses in block 76. For the matrix calculation, the twelve unused entries of that last block were filled with the functions implemented by the original gate sequence. This is a **fixed completion**. The experiment does not rule out a better matrix factorization under a different choice of those twelve unused entries. Rows beyond the valid domain were not changed in any submitted table, and no address relabeling was performed.

## Correctness and resource status

No new candidate was generated, so there is no new Q/T measurement or official competition score. The original family remains at **4033 loader CCX per pass**, with its existing **14728 total task Toffoli / 427 total task qubits** for the same geometry. Its previously established exact **36600-transition** proof remains applicable because the original files were unchanged.

The new checks are analyses of actual truth functions and the synthesis cost of specified candidate classes. They are not substitutes for the required independent output, workspace, and all-measurement-phase proof if a future candidate is emitted.

## What remains untested

- New multioutput XAGs that share newly synthesized products across output functions; the selected-basis matrix route does not search this larger class.
- Exact SAT synthesis of 5/6-input cones, particularly cones that cross cached-function generation and output accumulation while preserving all externally used intermediate functions. No SAT-optimality claim is made here.
- Sequences of cost-neutral transformations before a later reduction, or larger nonlinear cones.
- Batch 0's joint-product block across nonlinear control updates.
- Alternative completions of the unused twelve rows, and alternative output bases beyond the explicitly enumerated masks.
- Changing the angle-word coding or factorization jointly with a new generator. No table or selector change was attempted.

## Reproduction

Run from the workspace, with fresh output paths:

```bash
kickmix_venv/bin/python gvqcc_repo/chemistry_relation_screen.py \
  --loaders dqi_inputs/chemistry_4033 \
  --table dqi_inputs/chemistry_4033/submission.npz \
  --output-dir dqi_inputs/new_chemistry_relation_recheck \
  --report gvqcc_repo/chemistry_relation_recheck.json

kickmix_venv/bin/python gvqcc_repo/chemistry_relation_cofactor_rank.py \
  --loaders dqi_inputs/chemistry_4033 \
  --report gvqcc_repo/chemistry_relation_cofactor_recheck.json \
  --coded-parities

kickmix_venv/bin/python gvqcc_repo/chemistry_relation_context_check.py --loaders dqi_inputs/chemistry_4033 --table dqi_inputs/chemistry_4033/submission.npz --report gvqcc_repo/chemistry_relation_context_recheck.json
```

Omitting `--coded-parities` reproduces the smaller 7175-mask class, not the final expanded search.
