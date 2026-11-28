# QDLN: beyond local minima — actual post-HMR cost analysis (2026-11-22)

**Result: No new KMB and no score improvement. This is a new real-data screen, not an adoption candidate.** Baseline source is goodpjw2008 public V8 (3,375 paid three-qubit gates/pass), not the newer V9 (3,372).

## Entire ANGLE circuits: exact computational-support audit

A new bit-parallel simulator read the real KMB v2 opcodes of all 15 batches, following all 128 live quantum bits across every CX/X/CCX and HMR reset. The only reachable inputs enumerated were 1,219 addresses times two legal forward/reverse submitted-word states per batch (36,570 total instances). Z, CZ and conditioned diagonal corrections were ignored *only for computational-basis evolution*. The final selection, word and scratch states matched the exact expected output on **all 128 bits** in every instance.

- Baseline KMB: 3,375 three-qubit paid operations/pass, all 15 batches.
- Paid CCX with a control product zero on *all* 2,438 legal inputs: **0**.
- Paid CCX whose active control product lies in the affine GF(2) span of all other contemporaneously live qubits plus constant, excluding its target: **0**.
- Therefore no replacement of the restricted form CCX -> X/CX from the **unchanged native parent** is available at any pre- or post-HMR point. This does **not** imply minimum Toffoli complexity. New cache functions, circuit scheduling and cross-HMR transformations remain untested.
- Phase equivalence and measurement branches of a **modified** KMB have NOT been proved.

## New global bottleneck in five expensive restart batches

Five batches {0,1,5,7,11} have a 38-CCX segment between measurements (phase index 66 for batch0, 63 for the others). Over the actual legal input support, let V be the linear span of the 128 input wire truth tables and 1; let h_1,...,h_38 be the actual AND activations of the 38 paid gates; and let Y be all 128 wire truth tables *just before* the next HMR.

The independently measured GF(2) ranks are:

    dim(V)                          = 128
    dim(V + span(h_1,...,h_38))     = 166
    dim(V + span(Y))                = 159

Thus the 38 activations are linearly independent modulo the available input functions, but **only 31 independent nonlinear output functions survive at the end of the interval**. Seven is a dimension gap, NOT a certified 7-Toffoli implementation.

A separate exact GF(2) *variable projection* certificate checked all 38 possible single deletions while holding the other 37 gate activations fixed. For each omitted i, Y was not contained in V + span(h_j : j != i): **38/38 single deletions are mathematically impossible with fixed intermediate functions, even after arbitrary output XOR readout refitting**. The remedy is coordinated modification of the nonlinear intermediate functions, not merely changing output masks.

Across these five segments, 38 products each have nonzero final fanout; no pair of their formal quadratic forms shares a rank-3 factor span (zero 2->1 replacements). No triple of output effect masks had a zero-XOR relation among the same three gates (zero simple 3->2 reductions). These are only narrow, mathematically defined searches.

## Real PyTorch (not abandoned)

PyTorch 2.10.0+cpu was run against batch0/phase66 on the *real* post-HMR input registers. The causal two-layer XAG has 129 input features, 37 trainable AND gates, 31 affected output bits and 13,431 learned parameters. The unchanged 38-AND parent was exactly replayed. Training attempted a genuine **38 -> 37** reduction:

- 80-step native-warm-start run: smallest full-domain hard mismatches = **9,270**.
- 200-step higher-temperature / AdamW run: smallest full-domain hard mismatches = **6,666**; most later iterations deteriorated to ~37,000.
- Strict exact acceptance: **0**. New actual KMB saved: **none**. Kaggle score gained: **0**.

This identifies why the naive optimizer stagnates: at ±3 logits the hard circuit freezes; when logits are softened, discrete gate masks change too many bits simultaneously, destroying parent equivalence. Increasing trainable parameter count without enforcing GF(2) constraints is not a solution.

## A feasible next search, with an incumbent guarantee

Optimize **a full 38-product factor dictionary** under a projection to the target output subspace. Candidate generation may use PyTorch logits/STE, but exact GF(2) output readout must be solved after each hard proposal (variable projection). The optimizer should learn multiple simultaneous replacements, not try to delete one factor from an otherwise fixed dictionary. Score only complete native circuits:

    T_best(next) = min(T_parent, T_verified_candidate)

A candidate can be accepted only after all relevant reachable forward/reverse states match, phase and HMR corrections are exact, scratch clean and official physical FeMoCo/error constraints pass. Preserve 128Q cap and compare against public V9 at **3,372T/pass**.

The local reproducible research ZIP contains the exact bitset support simulator, GF(2) projection proof, actual PyTorch training scripts and results. Native KMB binaries are *not* re-distributed.
