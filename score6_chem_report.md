# Score6 chemistry: a verified small improvement and an exact gauge check

## Accepted local result

Two coefficient-only candidates passed the unchanged full chemistry verifier,
including all **78,080 shots**. The measured lower-cost endpoint improves the
retained score5 chemistry cost by **14.32199717**, or **0.00000485511%**. A
conservative interpolation keeps more numerical margin and improves it by
**3.03913671**, or **0.00000103026%**. These are very small cost improvements.
There is **no Toffoli reduction, qubit reduction, submission, or observed public
score improvement** in this experiment.

The comparison is against the exact chemistry retained in the score5 final ZIP:
NPZ `5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`,
with its actual fifteen 4033-per-pass loaders. It is not a comparison against
the separate v27 4030-loader result or the user's logged best lambda.

| Official metric | Retained baseline | Measured lower-cost endpoint | Conservative 20% interpolation |
|---|---:|---:|---:|
| Chemistry cost | 294988052.12610483 | **294988037.80410767** | **294988049.0869681** |
| Effective lambda | 46.906472675810164 | 46.90647039844889 | 46.90647219255269 |
| Error1, Ha | 0.01999998000005401 | 0.01999890416235086 | 0.01999976426910306 |
| Error2, Ha | 0.0199999936269957 | 0.019999999800000157 | 0.0199999948602906 |
| Gap, Ha | 3.9148980200006918 | 3.9148980000973097 | 3.914898016184452 |
| Raw Lambda | 282.96313136058893 | 282.9631054929985 | 282.9631258424406 |
| Error2 reserve, nHa | 6.3730043 | 0.1999998 | **5.1397094** |
| Gap reserve, nHa | 20.0006918 | 0.0973097 | **16.1844520** |
| ANGLE Toffoli per pass | 4033 | 4033 | 4033 |
| Total task Toffoli | 14728 | 14728 | 14728 |
| Total task qubits | 427 | 427 | 427 |
| Full verification shots | 78080 | 78080 | 78080 |

The smaller reserve in the measured best endpoint is explicit. The alternative
was constructed by taking exactly 20% of its W/H2 displacement from the retained
baseline; it was not another optimizer search. Both candidates passed all
official conditions locally. Neither lambda is below the user's independently
logged `46.905894137`.

### Correction of the earlier discrepancy note

An intermediate message incorrectly associated the earlier error values
`0.019998360…` and `0.019999998499…` with NPZ 5f8. Those values belonged to other
candidate/baseline records. The SHA-bound original 5f8 receipt reports exactly
the baseline values in the table above. The fresh numerical evaluation
reproduced that entire official metrics dictionary exactly. **No cross-platform
discrepancy was established.** The conservative interpolation is retained as a
margin-preserving alternative, not as a repair of a demonstrated platform error.

## What changed and how the candidate was obtained

Every one of the 91,500 angle words, the Givens tree, and all fifteen loader KMB
files remains byte-identical to the retained baseline. Only `W` and `H2_I`
changed. The search used two scalar directions: the difference from retained W
to the available v27 W, and the corresponding difference in H2_I. A bounded
two-variable constrained SLSQP search used the exact nonsmoothed fixed-angle
objective and analytic directional gradients, followed by unchanged official
numerical evaluation and then full circuit verification.

The accepted endpoint coefficients of those two directions are
`[-0.0007756918491591949, 0.0003053189812533447]`. The complete bounded search,
including model preparation, took 32.20 seconds and used less than 1 GiB peak RSS.
The conservative endpoint is the exact 20% interpolation of the saved arrays.

The original and new receipts use the same verifier SHA
`ca84ca08e6e9280922cda3b539d4776ae58990b2b03b5619a53d65de67df9d2b`.
The copied verifier receipts themselves label the baseline cost as a numeric
comparison because the optional receipt argument was not passed. The manifest
adds an independent explicit binding: the original official PASS receipt,
baseline NPZ hash, all fifteen loader hashes, full resource dictionary, and
baseline cost were checked against both new receipts. No new verifier run was
needed for that binding.

### Why the complete v27 coefficients were not transplanted

The v27 table differs from the retained table in **6840 words**. Only 387 of 1220
reconstructed vectors agree up to global sign within 1e-12; the largest signed
vector difference is 1.116562966860553. Thus this is not simply a different
angle representation of the same vectors.

With the retained words and W, the direct latest-v27 H2 substitution has
error1 `0.022389896793371784` Ha and fails. Substituting both v27 W and H2 while
retaining the old words has error1 `0.022103595784080204` and
error2 `0.02000542370918321` Ha and fails. Those invalid combinations were not
submitted or packaged as accepted candidates. The available 4030 cost was not
assigned to the actual 4033 circuits.

## A synthesis-aware modulo-angle experiment

The earlier `symmetry_chemistry_20261115_tags.py` established genuine angle
gauges of the form

\[
w'_j=(-1)^{s_j}w_j+128k_j\pmod{256},\qquad
\theta_j=\pi w_j/128.
\]

It also established that the five conserved word tags can be changed by a
globally consistent sign gauge. However, recompiling that zero-tag table with
the generic QROM constructor costs 18270 Toffolis per pass. The five original
tags also provide useful nonlinear address functions inside the 4033 circuit.
Consequently an abstract modulo identity does not establish a cheaper loader.

The new experiment holds the existing synthesis fixed and asks whether its
behavior outside the original tag values already implements useful alternative
gauges. For every valid address, it toggles any of the five first-batch MSBs and
propagates the resulting state through all fourteen unchanged subsequent
loaders. This covers **32 × 1220 = 39,040** address/tag cases. It explicitly
tracks selection, scratch, and every formal HMR phase coefficient.

For an ordered tree whose child is introduced with zero amplitude, each active
split of a vector has fixed sine and cosine magnitudes when the complete final
vector is fixed up to global sign. The exact integer condition is

\[
w'_j\equiv w_j\quad\text{or}\quad w'_j\equiv-w_j\pmod{128}.
\]

Integer quadrant signs then propagate the relative signs to every final
nonzero coordinate, which must share one global sign. Angles whose parent
amplitude is exactly zero are treated as unconstrained. The checker uses no
floating tolerance for either this equivalence predicate or the phase proof.

The canonical offset passes on all 1220 addresses. **Every one of the 37,820
noncanonical cases violates an active-angle magnitude condition.** All
measurement phases and scratch still cancel, so the failure is physical
vector equivalence, not a simulator or phase error. Clearing every tag is
possible without an offset only on the 459 addresses whose original tags are
already zero.

This excludes the tested cheap shortcut: changing the first five MSBs and
reusing all later circuits unchanged. It does not exclude gauge transformations
that also change lower first-batch bits, another synthesis, or approximate
tensor changes. No candidate circuit or Toffoli reduction resulted.

Separately, the existing exact HMR-tail contraction scan was applied to all 15
actual loaders. It examined 1115 HMRs and found no eligible last-write CCX tail.
This is a scoped negative result for that rewrite rule, not an optimality proof.

## Resource interpretation

The official cost is `lambda_eff × total_Toffoli × total_qubits` for this task.
The unchanged resource breakdown is 6662 heuristic Toffolis plus 8066 for the two
ANGLE passes. The fifteen loader circuits use at most 128 qubits. The official
inner state preparation contributes 303 temporary qubits, so reducing ANGLE
scratch alone does not remove that dominant term. The resulting total remains
`124 persistent + 303 temporary = 427` qubits. No custom change to the 303 term
was assumed or claimed.

## Candidate files and evidence

Measured lower-cost candidate:

- File: `/workspace/scratch/3815fb5fae06/score6_chem/transfer_full/submission.npz`
- SHA256: `16ee9ad3716309385aa9ce48c1f714e59484b79126ac6fe60591d3ba8bd7ebcf`
- Full receipt: `score6_chem_transfer_full_verification.json`
- Family digest from the verifier: `a06903f4554d6bb7cd3dc9d040b8a5969c25a42a23ad93a30b23030dd401769c`

Margin-preserving alternative:

- File: `/workspace/scratch/3815fb5fae06/score6_chem/backoff_full/submission.npz`
- SHA256: `99627e266340dd5fe71fff264d088024593310e1f06b2b15a61ef6108ee699c0`
- Full receipt: `score6_chem_backoff_full_verification.json`
- Family digest from the verifier: `29f4126f95b87be29f5817eae324703ca800feccded57010ee0f75bf0085f664`

Both use the unchanged files in
`/workspace/scratch/3815fb5fae06/score2_best_family/angle_k_0.kmb` through
`angle_k_14.kmb`. Full input, source, receipt, and candidate hashes are recorded
in `score6_chem_manifest.json`.

### Reproduction commands

Use a fresh output directory for each command. The scientific Python runtime
requires NumPy/SciPy; the tag checker requires KickMix. No browser, submission,
or network operation is involved.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score6_chem_transfer.py \
  --baseline /workspace/scratch/3815fb5fae06/score2_best_family/submission.npz \
  --portfolio /workspace/scratch/3815fb5fae06/score5_final_submission/submission.zip \
  --out /new/output/transfer --seconds 35

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python score6_chem_backoff.py \
  --baseline /workspace/scratch/3815fb5fae06/score2_best_family/submission.npz \
  --endpoint /workspace/scratch/3815fb5fae06/score6_chem/transfer/candidate.npz \
  --baseline-receipt score6_chem_baseline_verification.json \
  --out /new/output/backoff

kickmix_venv/bin/python score6_chem_tag_extension.py \
  --source /workspace/scratch/3815fb5fae06/score2_best_family \
  --out /new/output/tag_extension
```

The time-bounded optimizer is a search reproduction, not a byte-reproduction
promise for a different numerical stack or speed. The exact accepted arrays
and their hashes are preserved separately. For official verification, use
`score_dfthcsos_fixed_words_verify.py` with the selected candidate, unchanged
baseline/loaders, and the pinned official verifier; pass
`--baseline-portfolio-receipt score6_chem_baseline_verification.json` to bind the
comparison directly. The completed receipts above require no rerun.
