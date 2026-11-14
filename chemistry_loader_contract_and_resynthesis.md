# ANGLE 4033: exact resynthesis experiment and input-contract diagnostic

## Updated outcome: reachable-subspace correctness proved exactly

The existing 4033 family has now passed an **exact, nonsampled proof** on every input used by the forward and reverse batch algorithm: 1220 addresses × 15 circuits × 2 directions = **36,600 transitions**. All 40 output bits match the expected batch, selection is restored, scratch is zero, all **2230 formal HMR phase coefficients** cancel identically, and all **2230 R instructions** have zero input. Runtime was 1.903 s with 34.15 MiB peak RSS. See `chemistry_reachable_exact_proof.py` and `chemistry_reachable_exact_proof.json`.

This establishes the correct coherent mapping on the reachable input subspace, including inputs entangled with a reference system. The arbitrary-target counterexample below concerns a stronger extension of the oracle outside that subspace; it is not evidence that the actual chemistry algorithm is incorrect.

The current official-pinned README and `circuits.py` have also been obtained under `official_sources/current_pinned_dfthcsos/`, and both hashes match the Kaggle worker pins. The README retains both the XOR-oracle description at lines 236–250 and the allowance for constructions loading the simulated submitted words at lines 268–281. Submission interpretation should use this complete contract, rather than infer disqualification from arbitrary-target behavior alone.

Finally, the linear-span resynthesis was repeated on the **exact union of both allowed input batches**, without assuming arbitrary targets. It again found **0 replacements out of 4033 CCX**, in 3.980 s and 42.25 MiB. Every rebuilt circuit was independently checked on all 36,600 transitions and every measurement branch. See `chemistry_context_span_resynthesis.py` and `chemistry_context_span_resynthesis.json`. No candidate KMB was emitted because the reduction was zero.

### Exact structure of the target dependence

The follow-up `chemistry_tag_dependency_analysis.py` / `.json` proved, for every address and arbitrary initial target, that batches 1–14 have the form

\[
F_a(z)=z\oplus P_a(s),\qquad s_j=z_{8j+6}\oplus z_{8j+7},\quad j=0,\ldots,4,
\]

where `P_a` has degree at most two in these five tags and every `s_j` is preserved. The exact symbolic expansion was checked for all 40 output bits of every circuit. Batch 0 is the ordinary target-independent XOR load and initializes the tags. This check took 1.912 s and 19.18 MiB.

On the submitted table, all 15 batches have the same tags, exactly

\[
s^*(a)=(a_0a_1,\ a_0a_2,\ a_1a_2,\ a_0a_3,\ a_1a_3)
\]

on all 1220 valid addresses. Thus the arbitrary-target behavior is not an arbitrary malfunction; the circuit is explicitly exploiting conserved coded-word data. A generic wrapper could hide the original tags, substitute these five canonical functions, run the existing circuit, and restore the original tags. The straightforward wrapper needs five additional persistent scratch bits, however, increasing batches 1–14 from 125 to 130 qubits and violating the 128-qubit loader cap. That design was not emitted as a candidate. The exact reachable-context optimization does not require such a wrapper.

## Initial experiment

The implemented structural resynthesis found **0 CCX replacements out of 4033**, both on all 2048 selection-register values and on the 1220 valid addresses. This is a bounded negative result: it excludes a single CCX's control product already being in the GF(2) linear span of the other live wires and the constant. It does not prove optimality of the loader, of a block, or of a different nonlinear synthesis.

The experiment also found a separate input-contract distinction in the existing public loaders. They pass the forward/reverse batch verification, but batches 1–14 are not arbitrary-target XOR oracles. This was detected symbolically and independently reproduced using native Kickmix for batch 1. The exact reachable-subspace proof above now establishes correctness on the algorithm's coherent input states. **No baseline circuit was changed and no submission was made by this experiment.**

## 1. Structural hypothesis actually tested

The earlier audit had already excluded simple adjacent cancellations and duplicate full 40-bit difference words. The newly tested structure is broader: a product may be equal to the XOR of several existing, nonadjacent live wires even if no single wire or complete word duplicates it.

The checker represents each wire as a Boolean polynomial in the 40 arbitrary initial word bits. The coefficient of each monomial is a complete address truth table, packed into a Python integer. This is necessary because the original circuits borrow output bits as controls; treating the output as zero would incorrectly prove identities on a smaller input domain.

For each CCX, it computes the exact control product and asks Gaussian elimination for a representation using other live wires and a constant. A successful representation would permit X/CX gates in place of that CCX. No successful representation was found. At most 81 output monomials were needed. The script also checks that selection is restored, workspace is clean, and each HMR phase coefficient cancels exactly before its measurement bit is overwritten.

| Domain | CCX examined | CCX removed | Runtime | Peak RSS |
|---|---:|---:|---:|---:|
| All 2048 addresses, arbitrary 40-bit target | 4033 | 0 | 3.747 s | 21.31 MiB |
| Valid 1220 addresses, arbitrary 40-bit target | 4033 | 0 | 3.905 s | 21.00 MiB |

Results: `chemistry_affine_contract_2048.json` and `chemistry_affine_contract_1220.json`. The earlier `chemistry_affine_span_*.json` files recorded the same zero result before the explicit input-contract diagnostic was added. Use the newer reports with the current script.

## 2. Independent counterexample to an arbitrary-target XOR definition

Source: `dqi_inputs/chemistry_4033/angle_k_1.kmb`.

SHA-256: `e63f9de0a60ff79fc6f817056a1f95f5efed9ae82955cf56b11492e5ff28d70b`.

Native Kickmix was run on addresses 0–7 with each of 41 target patterns: zero and each individual set bit. This is 328 shots, using seed 123456789. The test is independent of the polynomial tracker and reads the original KMB directly.

| Diagnostic | Count |
|---|---:|
| Difference from `g(a,0) XOR z` | 80 |
| Difference from declared batch-delta XOR | 198 |
| Phase errors | 0 |
| Changed selection | 0 |
| Dirty workspace | 0 |

One counterexample, with the five 8-bit words concatenated little endian:

| Item | Value |
|---|---:|
| Address `a` | 0 |
| Initial target `z` | 64 |
| `g(a,0)` | 1081479393779 |
| Required `g(a,0) XOR z` | 1081479393715 |
| Actual `g(a,z)` | 215248526962 |

For this example, the submitted table's exact delta gives the same expected result as `g(a,0) XOR z`. The mismatch is therefore not just a choice of reference delta. This does not contradict a successful test on the previous batch's particular target state.

Reproduction script: `chemistry_native_contract_check.py`.
Result: `chemistry_native_contract_k1.json`.
The earlier short result is `chemistry_arbitrary_z_native_check.json`.

## 3. Contract evidence and version boundary

### Official companion paper

The competition overview links the Google Quantum AI paper [arXiv:2610.23832v1](https://arxiv.org/pdf/2610.23832v1). Its printed page 19, Section III.C.6, Equation (70), defines

\[
\operatorname{ANGLE}_k:\quad |a\rangle|z\rangle\mapsto
|a\rangle|z\oplus\Delta\vartheta_a^{[k]}\rangle.
\]

The accompanying text identifies the vector address as the only input/control, and describes each oracle as self-inverse. The paragraph after the box explains how this interface updates the reachable previous batch into the next batch. Thus the paper states a general XOR interface and explains a particular use of it. This is strong evidence for the intended interface, but is not a substitute for checking later competition amendments. The paper also contains older cost-model descriptions that differ from the known scoring receipts.

The PDF extraction shows the relevant material at lines 1684–1709. The HTML search extraction omits this boxed passage; the original HTML MathML `alttext` and the PDF both contain it.

### Available mirror

The following are exact locations in the local Inzainos mirror, not a claim that this mirror is the latest official bundle:

| File under `official_sources/Inzainos/verifiers/dfthcsos/` | Location | Observation |
|---|---|---|
| `SCORING_README.md` | 236–250 | “What a submission must do” defines the general XOR mapping. |
| `SCORING_README.md` | 268–281 | Describes forward/reverse simulation of the batch sequence. |
| `SCORING_README.md` | 283–306 | Explicitly distinguishes sampled evidence from proof for every target-register input. |
| `scoreinfra/circuits.py` | 9–15 | Declares the XOR oracle in the module documentation. |
| `scoreinfra/circuits.py` | 450–458 | Describes zero initial targets followed by the batch sequence. |
| `scoreinfra/circuits.py` | 522–555 | Reinitializes exactly the recovered batch between calls and checks the reverse sequence. It does not draw arbitrary target states. |
| `example_submission/angle_k_reference_circuit.py` | 19–28 | Defines a usual QROM/XOR reference construction. |

### Current official files recovered and pinned

The current Kaggle worker's pinned files were recorded in `kaggle_score_worker_build.json`, and the worker checked those pins. The earlier local copies have different hashes because each has one extra final newline; the README and `circuits.py` bodies are otherwise identical. This was a local byte-format difference, not evidence of a specification amendment. The exact pinned versions are now saved in `official_sources/current_pinned_dfthcsos/`. The independent provenance audit is `chemistry_current_contract_provenance.json` / `.md`.

| File | Local mirror SHA-256 | Kaggle worker pinned SHA-256 |
|---|---|---|
| `SCORING_README.md` | `304d546013312b2daf500942897c4d8b18bfe4a6658f4bf4653b40c12591721b` | `c2228569f96e58e118419bc32be2be9e33d6abffb8117cb0b91e1fc25b2a0230` |
| `scoreinfra/circuits.py` | `98601c25aa5f57ff7024c545f8773badc43ad2e6b586e6400bc2158c2bd01b86` | `fc027b52fdcebe14404f403a089122485d097ed65d03e6d989623d620b1ab68c` |
| `verify.py` | `ca84ca08e6e9280922cda3b539d4776ae58990b2b03b5619a53d65de67df9d2b` | `0775be7a528922367caebe9e4d051d6199811f1aefeaa4b793eaaa4621b8ec9d` |

The current README contains the same two relevant statements: the XOR description and the allowance for constructions that load the submitted words in the simulated sequence. The exact proof above strengthens the existing score evidence by proving the intended forward/reverse channel for all addresses and measurement branches. No new official failure was observed. The stronger arbitrary-target XOR extension remains false, but is distinct from reachable-subspace correctness.

### Why the exact proof also covers coherent quantum inputs

For fixed circuit `k`, write the allowed inputs as `|a>|batch_in(a)>|0_workspace>`. The checker enumerates every address and shows the exact output `|a>|batch_out(a)>|0_workspace>`. Each HMR outcome is treated as an independent formal variable; its phase coefficient is the measured Boolean function plus all corresponding conditioned phase corrections. The coefficient vanishes for every address before that variable is overwritten. All R inputs are identically zero.

Consequently every measurement branch implements the same basis mapping, multiplied only by the input-independent normalization from its HMR outcomes. For an arbitrary state `sum_a |a>|batch_in(a)>|r_a>` with an unrestricted reference/data system `|r_a>`, linearity therefore gives `sum_a |a>|batch_out(a)>|r_a>`, with no residual relative phase or correlation with the measurement record. Angle-controlled Givens rotations leave the angle-word register unchanged, so this proof applies at the successive forward and reverse calls in the algorithm.

## 4. Cost of a conservative strict-XOR repair

The mirror's ordinary QROM generator was rebuilt in memory using the unchanged `(1220, 75)` angle-word table, with precision 8 and batch size 5. The table SHA-256 is `3f864a7aeaa4d78984c8822761782b63be2d553b229f487e79640a73be147c44`. Every output-register use was checked to be a CX target, never a control or measured wire, so the arbitrary-target XOR structure follows directly from the construction.

| Resource | Public 4033 family | Ordinary QROM fallback |
|---|---:|---:|
| Loader CCX per forward pass | 4033 | 18270 |
| Maximum loader qubits | 128 | 61 |
| Maximum loader scratch qubits | 77 | 10 |
| Total task Toffoli, same geometry | 14728 | 43202 |
| Total task qubits, same geometry | 427 | 427 |

Each of the 15 reference circuits has 1218 CCX. The unchanged heuristic cost is 6662, hence `T = 6662 + 2 * 18270 = 43202`. Although the loader gets narrower, the inner state preparation's 303 temporary qubits still dominate. The total task therefore remains at `84 + 40 + max(303, 10) = 427` qubits. With the same factorization, this fallback's chemistry cost is 2.9333 times the current 4033 cost. It is a concrete conservative repair cost, not a lower bound and not the best possible strict-XOR synthesis.

Measurement took 1.319 s and 43.80 MiB peak RSS. It did not run the scoring verifier, change the factorization, save replacement circuits, or produce a new competition score. Code and result: `chemistry_xor_reference_cost.py`, `chemistry_xor_reference_cost.json`.

## Reproduction

Run from the project workspace, using fresh output paths:

```bash
kickmix_venv/bin/python gvqcc_repo/chemistry_affine_span_resynthesis.py \
  --loaders dqi_inputs/chemistry_4033 \
  --output-dir dqi_inputs/new_chemistry_affine_recheck \
  --report gvqcc_repo/chemistry_affine_recheck.json --addresses 1220

kickmix_venv/bin/python gvqcc_repo/chemistry_native_contract_check.py \
  --loaders dqi_inputs/chemistry_4033 \
  --table dqi_inputs/chemistry_4033/submission.npz \
  --report gvqcc_repo/chemistry_native_contract_recheck.json

kickmix_venv/bin/python gvqcc_repo/chemistry_xor_reference_cost.py \
  --generator official_sources/Inzainos/verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py \
  --table dqi_inputs/chemistry_4033/submission.npz \
  --report gvqcc_repo/chemistry_xor_reference_cost_recheck.json
```
