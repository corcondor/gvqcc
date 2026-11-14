# Bounded joint-product synthesis experiment

## Result

**No CCX reduction was found in the specified local tensor-rewrite class.** The source 4033 family, scoring worker, and submission artifacts were not modified. No candidate KMB was emitted, no official scoring run was started, and no external push or submission was performed.

The executable experiment is `chemistry_joint_product_resynthesis.py`; the authoritative completed result is `chemistry_joint_product_verified.json`. The earlier `chemistry_joint_product_resynthesis.json` records the initial screening before the normalization proof was added.

## Exact search class

The source circuits mix high-address and low-address functions through CNOT basis changes. The experiment therefore does not assume that each literal CCX control is already a separate high/low factor. Instead, it expresses both controls as affine Boolean forms in one common entry frame, and propagates each CCX target through the subsequent output CNOT network into one common exit direction.

This yields terms `u * v * w`, where `u` and `v` are Boolean control functions and `w` is a bit vector specifying the output direction. The search includes:

1. Combining two terms sharing any two factors, by XORing their remaining factors.
2. Exact Boolean quadratic-form decomposition for all terms with the same output direction. Diagonal products use `x*x=x`; any resulting affine correction is retained as X/CX gates.
3. A shared-factor XOR flip of two terms, followed by an immediate merge with a third term. For example,

   `A*B*C XOR A*D*E = A*(B XOR D)*C XOR A*D*(C XOR E)`.

   Control factors are commutative, so both orientations are considered. An improvement would restart the search greedily.

The identities preserve the complete Boolean operation of the extracted block. Final checking nevertheless uses the independently implemented exact reachable-subspace proof, including both specified batch inputs and all measurement outcomes.

## Coverage and measured result

| Batch family | Extracted products per circuit | Circuits |
|---|---:|---:|
| k=1,2,3 | 212 | 3 |
| k=4,5,7,9,11 | 189 | 5 |
| k=6,8,10 | 187 | 3 |
| k=12,13,14 | 188 | 3 |
| k=0 | Outside this extraction class | 1 |

The 14 extracted blocks contain **2706 CCX products**, and **260835 pairs** were screened. Within each block, every output direction is distinct, and every one of the `2*n` control forms is distinct. Consequently:

- Two-factor merges: 0.
- Repeated output directions eligible for quadratic-rank reduction: 0.
- Shared-factor pairs eligible for the tested flip: 0.
- CCX removed: 0.

Batch 0 has a nonlinear update of a control/workspace wire inside the span of its output accumulation gates. The extractor rejects that block instead of moving products across the dependency. This experiment makes no claim about its joint-product optimization.

The verified run took **4.534 s** with **52.64 MiB** peak RSS. A 480-second runtime guard was configured but was not approached; the search ended because its eligible transformations were exhausted.

## Check of the normalization itself

A zero-hit search would not be informative if the frame conversion were wrong. Therefore all 14 extracted circuits were reconstructed from their unchanged normalized products, with all original CCX gates removed from the linear skeleton and the reconstructed products added in the exit frame.

The independently implemented truth-table/measurement-phase checker proved both directions for all 1220 addresses of every reconstructed circuit: **34160 address transitions**. Output words, restored selection, clean scratch, zero R inputs, and every formal HMR phase coefficient passed. CCX counts and qubit counts matched the originals. These reconstruction circuits remained in memory and were not saved as candidates.

The unchanged batch 0 is covered by the already completed `chemistry_reachable_exact_proof.json`, which proves the original full family on all **36600** transitions. The complete original-family proof remains valid because no original files were changed.

## Limits of the conclusion

This result excludes only the specified exact-factor sharing and one-flip local rewrites in the extracted linear frame. It does not exclude a sequence of cost-neutral transformations before a reduction, a larger tensor decomposition search, identities that exploit nonlinear relations among the entry features, changes to the encoded angle words, or optimization across a nonlinear control update. It does not establish global or local optimality under those broader classes.

The chemistry resource counts remain **4033 loader CCX per pass**, **14728 total task Toffoli**, and **427 total task qubits** for the existing geometry. These are unchanged known resource figures, not a new measured competition score.

## Reproduction

Run from the workspace with unused output paths:

```bash
kickmix_venv/bin/python gvqcc_repo/chemistry_joint_product_resynthesis.py \
  --loaders dqi_inputs/chemistry_4033 \
  --table dqi_inputs/chemistry_4033/submission.npz \
  --output-dir dqi_inputs/new_chemistry_joint_recheck \
  --report gvqcc_repo/chemistry_joint_recheck.json \
  --seconds 480
```
