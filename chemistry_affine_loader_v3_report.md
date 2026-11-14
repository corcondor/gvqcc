# Address-affine patches to the 4033-Toffoli ANGLE loaders

## Result

The implementation `chemistry_affine_loader_v3_build.py` creates new angle tables and matching patched circuits without increasing Toffoli count or qubits. The concrete example in `chemistry_affine_loader_v3_example/` changes angle column 0 bit 0 by XOR with selection/address bit 0. This changes 610 of the 91,500 words. Only two circuits change: batch 0 gains a final `CX q0 q11`, and batch 1 gains an initial `CX q0 q11`. The remaining 13 KMB files are byte-identical to the original family.

The complete family remains **4033 Toffoli per pass, 8066 for forward plus reverse, and at most 128 qubits per circuit**. The NPZ retains all arrays except `angle_words`, including the tree and array shapes. This establishes a loader construction method; it is not a physical-accuracy or score improvement result.

The repository stores the small example coefficient array and its proof, rather than duplicating the generated full factorization and all fifteen KMB files. Recreate the complete example with `python chemistry_affine_loader_v3_build.py --coefficients chemistry_affine_loader_v3_example/coefficients.npy --out fresh_example_directory` under a Python environment with Kickmix and with the pinned source loaders available. The generated files were inspected locally; they are an experimental example, not a validated chemistry submission.

## Interface and address mapping

`patch_words(words, coefficients)` uses only numpy, so the physics optimizer does not need to import Kickmix. `words` must be an integer array of shape `(1220,75)` with values in `[0,255]`; `coefficients` must be an integer array of shape `(75,8)` with values in `[0,4095]`. Coefficient bit 0 selects a constant XOR, while bits 1 through 11 select address bits 0 through 10. All selected Boolean terms are XORed. The output has the same dtype and shape as the input.

Addresses are precisely the verifier's integer addresses 0 through 1219, with little-endian selection register `q0..q10`. They comprise 76 one-body rows followed by 8 × 143 two-body rows, according to `scoreinfra/dfthc_math.py`. An affine predicate can affect both portions: preserving the first 76 rows requires a separately checked restriction and is not automatic. The five 8-bit output registers occupy `q11..q50`; 75 angles require 15 batches with no padding.

Example:

```python
import numpy as np
from chemistry_affine_loader_v3_build import patch_words, build_affine_family

coefficients = np.zeros((75,8), dtype=np.uint16)
coefficients[0,0] = 2  # angle column 0, LSB, XOR address bit 0
new_words = patch_words(old_words, coefficients)
# Run the chemistry objective and error constraints on new_words first.
# Then run under the Kickmix Python environment:
circuits, new_words, report = build_affine_family(
    coefficients,
    output_dir="fresh_candidate_directory",
    native_seeds=(20261115,20261116),
)
```

The CLI accepts `.npy` or JSON coefficient arrays. `--table` can supply a factorization whose continuous parameters have been refitted, provided its old angle words are still those implemented by the source loaders. Exact proof rejects a mismatch. An output directory must be new. No output files are written before all required exact and requested native checks pass.

## Forward and reverse contract

Let `b[k](a)` be the original five-word batch at address `a`, `delta[k](a)` the affine bit patch, and `b'[k]=b[k] XOR delta[k]`. Set the previous batch and previous patch to zero before batch 0. In execution order the patched loader is:

1. XOR `delta[k-1]` into the word registers.
2. Execute the original batch-k circuit unchanged.
3. XOR `delta[k]` into the word registers.

This gives the intended forward map on the reachable input batch. The official verifier then executes **the same circuits**, in reverse batch order; it does not invert each gate sequence. See `official_sources/Inzainos/verifiers/dfthcsos/scoreinfra/circuits.py` in `recover_words_from_circuits`. Thus forward correctness alone is insufficient.

The existing exact output-polynomial audit (`chemistry_tag_dependency_analysis.py/.json`) shows that batches 1–14 update an arbitrary target by a function of the address and five preserved tags `s[j]=word[j].bit6 XOR word[j].bit7`. This provides a useful sufficient family: arbitrary affine changes to bits 0–5, and high-bit patches whose bit6-XOR-bit7 mask is the same across all 15 batches for each word slot. Patching both high bits with the same mask is a simple safe subfamily. Batch 0 is target-independent.

The implementation always runs the exact proof, regardless of the sufficient-family test. A deliberately unsafe patch to batch 1 bit 6 was rejected at `k=1/reverse`, address 0, slot 0, bit 0. This confirms why unconditional generic-XOR treatment would be incorrect.

## Verification and scope

The mandatory proof symbolically evaluates all **1220 addresses × 15 batches × 2 directions = 36,600 transitions**, checking all 40 output bits, unchanged selection, zero scratch, zero-input resets, and exact cancellation of each formal HMR measurement phase. It covers every classical measurement record, rather than sampling those branches. The example cancels 2230 formal HMR variables across these transitions. Because basis output maps and phases agree for all addresses, the reachable-subspace mapping also holds for coherent address superpositions.

After KMB serialization, all 15 emitted circuits were reloaded and the complete proof repeated successfully; `chemistry_affine_loader_v3_serialized_proof.json` records their hashes. Two native verifier seeds, each covering all addresses in both traversals at one shot per address, also passed. These are loader checks, not full competition shots.

Further in-memory checks in `chemistry_affine_loader_v3_checks.json` establish that a last-batch constant patch restores correctly on the reverse boundary, equal bit-6/bit-7 patches pass, and a varying-tag patch is rejected before any files are written.

No chemical tensor-error evaluation, continuous refit, official full-shot validation, submission, or score improvement is asserted for the example. Once the physics optimizer finds a useful coefficient array, the same construction can generate and prove the corresponding loaders at unchanged Toffoli count.

## Hashes

- Builder: `c9d7f66105b669be8d21094743684f38055468da79d2cede6e16141cb5454b84`
- Source factorization: `809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5`
- Example factorization: `4ac351cc479a450ec926f2c3d0400d9795777003518c84d34753660fc13a9f9c`
- Example batch 0 KMB: `622eba5887ecf3e6aee891a151798c555233b407f6afad298bbce3ce3bbd12db`
- Example batch 1 KMB: `577e67f72e33bf68f7e5e93a93457a565c556491f0afc1086e26218d9d6abd54`

All original files were read only. New files use the `chemistry_affine_loader_v3_` prefix.
