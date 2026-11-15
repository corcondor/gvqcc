# GVQCC: Verified ANGLE circuit evolution

This folder implements an **evaluator-guided code evolution target**, based on the same research pattern as Gu et al. (2026, arXiv:2610.22367): generate executable circuit synthesizers, run an **independent** exact evaluator, and keep only lower-cost circuits. `candidate.py` is the LLM-editable program; `evaluator.py` is never changed by the search.

## Pinned benchmark

- Existing portfolio: Score10, local calculated score **27.327844395957978**; chemistry 4,030 unconditional CCX over 15 ANGLE circuits.
- Comparison holds the original chemistry factorization, 75 Givens angle columns, and other two tasks fixed.
- The evaluator verifies all 1,220 legal addresses, 15 forward + 15 reverse transitions = **36,600**, and proves cancellation of **2,230 independent HMR measurement phases** in the original baseline.
- `combined_score` is the **ratio** of the predicted competition score to 27.327844395957978, not the actual Kaggle leaderboard score. An unchanged circuit scores exactly 1.0.
- The test proves exact equality on the **reachable input states** in the batch sequence, NOT correctness as an arbitrary-target XOR oracle. If the competition requires that stronger contract, candidates need an additional validator.
- Kickmix and the official competition verifier are intentionally not replaced. A locally successful candidate must subsequently pass the **unaltered official Kickmix verifier** and the chemistry numeric limits before being called a new validated submission.

## Setup and run

```bash
# Install on your own Codespace or Linux Python environment.
python -m pip install openevolve numpy
python bootstrap.py /absolute/path/to/score10_verified_components_combined.zip --out inputs
python evaluator.py candidate.py
python local_evolution.py --output runs/local

# API-backed LLM evolution; use a secret, never put the key in the repo.
export OPENAI_API_KEY=...  # supply via Codespaces / Actions secret manager
openevolve-run candidate.py evaluator.py \
  --config config.yaml --iterations 200
```

OpenEvolve is the **external program mutation/search engine**; this folder provides the problem-specific, fail-closed evaluator, exact circuit simulator, and initial mutation operators. `local_evolution.py` does deterministic smoke evaluation only, **not** LLM evolution. The Python modules use the standard library except the optional OpenEvolve runtime.

## Why this is better than local gate guesses

`candidate.py` may change the Python synthesis algorithm to implement algorithmic redesign, not just a fixed peephole. The evaluator rejects invalid circuits, checks register maps, scratch, resets, every measurement branch's phase correction, the 128-qubit ANGLE cap, and live output words. Only a genuine CCX decrease can increase the scored metric; X/CX reductions are tracked separately as a secondary feature.

A candidate with `toffoli_savings > 0` that passes this evaluator is **a new locally exact circuit**. Repackage it with the unchanged Score10 DQI/invsqrt/NPZ files and run the unchanged official verifier. The supplied checker is not a substitute for the official verifier. Never use test-seed manipulation, data-dependent correctness shortcuts, or an altered official cost model.

### Limitations

- Only the existing J=5, 15-batch, exact-angle family is evaluated here. To search different `J` and angle-gauge families, extend the metadata contract and full chemistry cost model first; the evaluator deliberately rejects them otherwise.
- A change to the angle words or numerical factorization needs a fresh chemistry-accuracy verification; the evaluator does not silently accept it.
- `kickmix` is not installed in the artifact's source runtime; the included KMB v2 reader/writer was round-trip-tested on original ANGLE KMBs.
- The seed's same-control and common-target CCX identities are correct on arbitrary quantum states, but a **4,096-op window scan found no new applicable two-CCX merge** on the 4,030 baseline. To improve the score, evolve genuinely different algorithms, intermediate value representations, or nonlinear synthesis strategies.

## Primary references

- Gu et al., *Discovering state-of-the-art quantum circuits with large language models*, <https://arxiv.org/abs/2610.22367> (paper and <https://github.com/andigu/uncompute>).
- OpenEvolve, <https://github.com/algorithmicsuperintelligence/openevolve>.
