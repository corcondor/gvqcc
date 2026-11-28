# QDLN — Quantum-Cost-Aware Differentiable Logic Networks

Independent, experimental research prototype based on the ideas of **Griffith** (differentiable LUT networks and verified IR), adapted to reversible quantum-classical logic synthesis.

Upstream: https://github.com/tsukushi-gate/Griffith (Apache-2.0; original work by the Griffith contributors). We did **not** fork the complete upstream repository: this GitHub integration does not expose a fork action. We are independently implementing the cost model and preserving attribution.

## Mathematical model

For n Boolean inputs, any quadratic output admits

    f(x) = c ⊕ (a·x) ⊕ ⨁_{i<j} b_ij x_i x_j.

The polar matrix B=(b_ij) is alternating over GF(2); a single product of two linear parities has polar rank at most 2. Thus a single output needs at least rank(B)/2 AND nodes. Symplectic decomposition reaches the bound for quadratic outputs, up to affine corrections which use only X/CX gates.

For multiple outputs, search a shared basis of rank-2 quadratic forms whose span includes the output forms. This is a finite, certifiable optimization for n=4, not a proof that arbitrary large XAGs are optimal.

Each product of two parities can be reversibly implemented by conjugating CCX with an invertible CNOT basis transform of the input register, using one scratch target. Output XOR fanout is done with CX and the scratch is then uncomputed using reverse CCX. The conservative resource cost is:

    Toffoli-equivalent = 2 * number_of_products
    qubits = input_width + output_width + number_of_products.

This is a **clean XOR-oracle** construction, not a measurement-based-uncompute optimization. No KickMix phase verification is implied.

## Actual experiment — public GVQCC 3,375T ANGLE data

Source chemistry table: public goodpjw2008 V8 ANGLE 3,375-Toffoli family, SHA-checked in the local research run.

- Scanned 1,140 16-address (low-four-bit) slices across 15 ANGLE batches.
- 994 slices had some quadratic-or-affine output functions (high-degree outputs excluded).
- 594 slices admitted an exact reduction relative to the independent shared-ANF baseline.
- Example: batch 2, high row 58, nine eligible output bits: 6 naive ANF quadratic products -> 2 shared XAG products.
- An actual differentiable candidate-selector recovered the two-product solution on those nine bits after 31 training steps (first seed).
- All 16 x addresses and all 512 initial nine-bit target states were exhaustively checked by the reversible gate-list simulator: input restored, target XORed, all scratch zero, no phase gates. The micro-oracle uses 4 CCX, 75 CX and 6 X, with 15 logical qubits.

**Do not add the per-slice savings to the full ANGLE circuit.** The published 3,375T loader already shares products over high address rows, caches, scratch, and retained gauge bits. A new 18-file submission, hosted verifier PASS, or scoreboard gain has NOT been achieved by this prototype.

## Research next step

1. Make the differentiable learned feature dictionary globally shared across high address rows and all five output words; model exact high/low ANF and cached low monomial overhead.
2. Optimize and emit entire ANGLE_k from a learned factored Boolean network. Prove the full reachable-domain forward/reverse mapping, HMR branches, selection/scratch, and 128Q bound.
3. Optimize the *actual* global lambda_eff * Q * T cost jointly with constrained FeMoCo refitting of angle_words, W and H2_I. Hard reject candidates whose official physics constraints fail.
4. Compare with latest published 3,372T/pass chemistry, not only the 3,375T historical circuit; attribute every source.

Source under research/qdln in this branch is Apache-2.0-compatible original experimental code. There is no copied Griffith implementation.
