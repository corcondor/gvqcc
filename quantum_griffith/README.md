# Quantum Griffith — exact quantum-Boolean circuit search (experimental)

An **independent experimental quantum extension inspired by [Griffith](https://github.com/tsukushi-gate/Griffith)**, not an upstream fork or an official Griffith module. This implementation does not copy Griffith source. Griffith is licensed Apache-2.0; cite its authors and the underlying differentiable-logic research when deriving further work.

## What is implemented

* Exact **reversible oracle IR** made from X, CX, CCX; deterministic basis simulator; gate/depth/ancilla report and JSON serialization.
* Exact **algebraic normal form (ANF)** compilation using the Boolean Möbius transform.
* Shared **XAG-like product-prefix DAG**: intermediate AND products are reused across multiple monomials and outputs; compute/uncompute returns every ancilla to zero.
* Cost-guided **invertible GF(2) affine basis search** using CNOT moves and an exact inverse. This changes the polynomial representation *without changing the logical function*.
* **Learned two-input LUT DAG lowering** with liveness pruning and Boolean CSE. Any two-input Boolean function is decomposed into affine operations plus at most one CCX to compute its output. Shared temporary nodes are uncomputed in reverse.
* Optional **PyTorch differentiable LUT architecture search**: gate truth tables, input wiring and output references are learnable via STE / Gumbel. Exact hard evaluation is a required acceptance test, not a soft-score proxy.
* Exhaustive equivalence tests and GitHub Actions CI. The fallback ANF compiler is exact even when an NN candidate fails training.

**This is a quantum *circuit-design learner*, not a claim of quantum advantage or a trained model executing inference on quantum hardware.** There are no approximate relative-phase Toffolis in this prototype. An arbitrary superposition inherits the correct oracle because every emitted gate is a phase-free permutation; after uncompute the work register returns to its initial |0> state.

## Run it (Python >= 3.10, standard library only)

From the root of the GVQCC repository:

~~~shell
python -m unittest discover -s quantum_griffith/tests -v
python -m quantum_griffith --case affine-product --inputs 4
python -m quantum_griffith --case shared-cubic --inputs 4
python -m quantum_griffith --case random --inputs 4 --outputs 3 --seed 21
python -m quantum_griffith --case affine-product --emit /tmp/circuit.json
~~~

The affine-product example is defined by

    f(x0,x1,x2,x3) = (x0 XOR x1) AND (x2 XOR x3).

Its vanilla ANF uses four CCX gates. A two-CNOT input-basis change can
represent it with one CCX, then undo the basis with two more CNOTs.
This gives **4 → 1 CCX** while preserving a clean exact oracle.
The CLI checks every input combination and every output-register value.

## Optional neural search (requires PyTorch)

~~~shell
python -m pip install torch
python -m quantum_griffith --case affine-product --inputs 4 \
  --train --train-gates 12 --train-steps 400 --train-restarts 3
~~~

The differentiable learner uses a continuous relaxation solely for training.
A *hard* learned DAG is accepted only after a full truth-table comparison.
It is then compiled to an exact clean reversible circuit. When no exact
candidate is discovered, the report says so, and the deterministic
ANF/affine solution remains available. **No unverified neural candidate
is silently substituted for a circuit.**

## Cost model and provenance

The objective minimizes

    ccx + 0.18 * clean_ancillas + 0.015 * cx + 0.0001 * depth.

This is an experimental proxy, not the Kaggle/KickMix cost function.
The optional "t7_estimate" column is a simple 7-T-per-exact-CCX
decomposition estimate; it is *not* a certified minimal T-count.
The exact measured resource numbers are computed after lowering, not
deduced from a differentiable loss.

| Cost source | Included? |
| --- | --- |
| Logical X/CNOT/Toffoli counts, width and greedy depth | Yes |
| Initial work qubits zero, output XOR, all work restored | Verified exhaustively for small n |
| Exact relative phase | Guaranteed by X/CX/CCX alphabet |
| Physical connectivity, T-depth, Clifford+T synthesis | Not yet |
| Classical GF(2) basis search | Yes |
| Learned wiring and 16 Boolean gate types | Experimental, optional |
| Strict GVQCC/Kaggle simulator and score | **Not integrated** |

## Important limitations and next research tasks

1. **Memory-aware recomputation/pebbling:** global cached prefix products may consume too many ancillas. Add dynamic work-line scheduling and compare *actual* peak width and CCX.
2. **Quantum-specific costs:** parameterize the T-cost of exact CCX/CCZ, phase gadgets, clean/dirty ancillas and hardware restrictions. Never treat a relative-phase substitute as equivalent without a full phase proof.
3. **Multiple levels of search:** combine a neural proposal generator, affine rewrites, graph resynthesis, SAT-based equivalence, and *exact* quantum resource feedback; maintain a Pareto front in (CCX, Q, depth).
4. **Multi-output learned circuits:** select intermediate computations jointly for all outputs instead of independent lookup-table costs.
5. **External benchmark:** integrate DQI finite-field kernels and chemistry angle-loader *isolated fixtures*, only then run the official GVQCC verifier. Until that point, **no claim of Kaggle score improvement** is justified.

### Notes on the classical source

Griffith implements differentiable LUTs, hard collapse, SAT capacity checks,
gradient-guided flips, don't-care resynthesis, HDL export, and wiring search.
The files most relevant as upstream references are
[griffith_logic/layers/lut.py](https://github.com/tsukushi-gate/Griffith/blob/main/griffith_logic/layers/lut.py),
[analysis/sat_capacity.py](https://github.com/tsukushi-gate/Griffith/blob/main/griffith_logic/analysis/sat_capacity.py),
[analysis/guided_flip.py](https://github.com/tsukushi-gate/Griffith/blob/main/griffith_logic/analysis/guided_flip.py),
and [export/dc_resynth.py](https://github.com/tsukushi-gate/Griffith/blob/main/griffith_logic/export/dc_resynth.py).

For broader prior work, see Petersen et al., **Deep Differentiable Logic Gate
Networks** (NeurIPS 2022) and the established literature on reversible logic
synthesis and differentiable quantum architecture search. No first-of-kind
claim is made.
