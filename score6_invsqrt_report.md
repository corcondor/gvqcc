# score6 invsqrt: exact modular phase analysis and joint phase rewrites

## Outcome

No new invsqrt benchmark candidate is accepted in this branch. The unchanged
`684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a` circuit remains
the incumbent: Q46, 1,550 static Toffoli-like gates, verified mean
1,478.7506100300882, effective count 1,710.2946813836015, and cost
78,673.55534364567. Its existing official receipt is
`score3_invsqrt_full_verification.json` (200,540,928 shots, PASS). No submission
or baseline mutation was performed.

This work implemented two new, bounded analyses prompted by the question about
modular arithmetic and the Bloch sphere:

1. An exact integer-lattice certificate proves that reweighting the **same 38
   phase predicates** cannot exploit whole-turn identities to remove a paid
   rotation. It covers arbitrary real coefficient changes, the four existing
   Clifford predicates, and an optional constant phase.
2. A joint identity for eight nested phase pairs was implemented and searched
   at the actual circuit's live cuts. It yielded no benchmark reduction within
   the stated affine and one-AND search families. A separate executable control
   reduced four Toffolis to three while preserving all phases, inputs, and clean
   scratch; that control is explicitly synthetic and is not a benchmark gain.

## The official contract already uses phase modulo one turn

The unchanged verifier is
`/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py`,
SHA256 `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`.

It requires every integer x from 1 through 3,133,452 to implement phase
`1/sqrt(x)` turns to tolerance `2^-24/sqrt(x)`, restore the 22-bit input, and
clean every other qubit. The phase comparison is already modulo one turn,
using uint64 units of `2^-64` turns. `Z_POW q alpha` uses half-turn units and
implements `diag(1, exp(i*pi*alpha))`.

The cost is `Q * (mean_Toffoli + rotation_T/4)`. A Clifford `Z_POW` is free;
a T-class angle costs one T. Each generic rotation is assigned
`0.56*log2(1/epsilon)+5.3` T by the verifier, with epsilon determined by the
remaining worst-case error margin. The incumbent has 33 generic rotations,
one T-class rotation, and four Clifford rotations. Thus a smaller drawn
circuit or fewer CNOTs alone does not improve this score.

The Bloch sphere identifies states up to global phase. This oracle's output
is itself a phase, so that identification cannot be used to erase the phase
that must be preserved across the superposition of input values. In formulas,
`Z_POW(alpha) = exp(i*pi*alpha/2) * Rz(pi*alpha)`; the prefactor must be tracked.
Also, `Rz(theta+2*pi) = -Rz(theta)`, although the Bloch rotation has returned
to the same orientation. These identities are useful only with their phase
factors retained. No arbitrary non-diagonal SU(2) synthesis was inserted into
the reversible arithmetic tape.

## Exact fixed-feature modular certificate

`score6_invsqrt_modular_certificate.py` extracts the Boolean value present at
each of the 38 `Z_POW` instructions in the accepted KMX. It evaluates all
3,133,452 legal inputs in packed truth tables. The circuit's 702 conditional
blocks are verified to restore their quantum data at each block boundary on
that full domain. The phase predicates are therefore independent of those
classical branch choices. Direct conditional operations outside these blocks
are restricted to the observed phase/classical operations.

Let `f_0(x)=1`, with `f_1,...,f_38` the unchanged rotation predicates, and let
`delta` be a vector of coefficient changes measured in **turns**. Exact phase
equivalence on this fixed basis means

`sum_j delta_j f_j(x)` is an integer for every legal x.

The certificate supplies 40 legal input values and their 40-by-39 binary
evaluation matrix A. Two 39-by-39 submatrices have exact determinants −3 and
−2. Their coprime determinants imply a full integer row lattice. More
constructively, the JSON publishes an integer matrix B and verifies `B A = I`.
Consequently, if `A delta` is integer, then `delta = B (A delta)` is integer.
Every coefficient change is therefore a whole turn and changes no rotation
class or required predicate.

This proof is stronger than a dyadic or GF(2) rank check: delta may have
arbitrary real entries. The 40 witness rows were independently replayed by a
scalar Boolean interpreter, and both determinants and the integer left
inverse were checked exactly with SymPy. The certificate can be checked
without trusting the full-domain truth table files.

**Scope:** this proves only the absence of a nontrivial exact modular
coefficient identity on the existing 38 predicates plus a constant. It is
not a lower bound for a circuit with new predicates, changed arithmetic,
different approximation, or different ancilla scheduling.

## New joint nested-phase rewrite

For Boolean functions with `g <= f`, define `h = f XOR g`. Pointwise integer
arithmetic gives `h=f-g`, hence the exact identity

`alpha*f + beta*g = (alpha+beta)*f - beta*h`.

This is useful when h is cheaper or available earlier than g. It preserves
the full phase, not only the Bloch orientation. Existing score2 searches
relocated g individually; the new search targets the **joint complement h**.

Eight such nested pairs were confirmed over every legal input. Their base
rotation lines in the accepted KMX are 8079, 8140, 8193, 8208, 8251, 8261,
8297, and 8318. The paired subset rotations are at lines 8090, 8148, 8200,
8210, 8255, 8264, 8306, and 8322. Four subset gadgets use two ANDs.

| New search | Evaluated scope | Result |
|---|---|---|
| Joint complement as an affine parity | 8 targets; 2,532 depth-zero CCX/CSWAP/HMR cuts; 20,256 queries; 4,608 legal sample rows | No model |
| Joint complement as one product plus an affine parity | 4 two-AND targets; 2,034 cuts with a full-domain-zero scratch; 17,266,156 queries; 512 stratified legal rows | No model in the searched left-factor family |

The one-AND solver tries 2,163 left parities: any single wire, any pair of
wires, or any parity of q22..q25 and q7 combined with one wire. Its right
factor and affine remainder are unrestricted live affine combinations. It
uses the unchanged, source-hashed score2 GF(2) quotient solver. A negative
linear system on a subset of legal rows excludes that identity on the full
domain. Every positive sample model would have been checked against all legal
inputs before emission; no positive sample model was returned.

The affine search took 5.72 seconds. The one-AND search completed in 38.82
solver seconds, within a 110-second external budget. This is a finite
negative result for the stated factors and cuts, not an unrestricted AND
complexity theorem. In particular, arbitrary longer left parities or changed
arithmetic are not exhausted.

The synthetic positive control implements the same joint identity with
`f=a`, `g=a*b`, `alpha=3/32` half-turns, and `beta=5/16` half-turns. It reduces
static and measured Toffolis from four to three, keeps Q24 and two generic
rotations, and preserves the exact phase. All 48 relevant input/measurement
branch cases pass an exact Fraction-based interpreter. Native Kickmix checks
also pass 512 inputs under two fixed seeds for each circuit (2,048 shots
total), with zero phase, input-restoration, or scratch failures. The files
are named `score6_invsqrt_joint_positive_*` to prevent confusion with a real
invsqrt candidate.

## Relation to primary literature

- Amy and Mosca, [T-count optimization and Reed-Muller codes](https://arxiv.org/abs/1601.07363),
  relate phase-polynomial optimization to code decoding, including finite-order
  rotations. This motivated checking exact coefficient relations instead of
  treating each rotation independently. The present integer-lattice result is
  a certificate for this circuit's fixed predicates, not a claim to have run
  a complete Reed-Muller optimizer.
- Amy and Lunderville, [Linear and non-linear relational analyses for Quantum
  Program Optimization](https://arxiv.org/abs/2410.23493), extend phase folding
  through affine and nonlinear relations with classical control. This
  motivated testing the relation `g<=f` jointly and validating branch-restored
  predicate values. A full nonlinear relational compiler was not implemented.
- Gidney, [Halving the cost of quantum addition](https://arxiv.org/abs/1709.06648),
  describes temporary logical ANDs with measurement-based erasure. The baseline
  already uses this principle heavily. The positive control retains the HMR
  phase correction rather than treating reset as a free deletion.
- Kliuchnikov et al., [Shorter quantum circuits via single-qubit gate
  approximation](https://arxiv.org/abs/2203.10064), give the mixed-fallback
  rotation cost used by the verifier. A different drawing or private synthesis
  estimate cannot override the official tariff.

## Reproduction and retained artifacts

Run from `/workspace/scratch/7f542e06b7cf/gvqcc_repo`:

```bash
python score6_invsqrt_modular_certificate.py --out /tmp/score6_invsqrt_certificate.json
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score6_invsqrt_joint_phase.py --out /tmp/score6_invsqrt_joint
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score6_invsqrt_joint_oneand.py --out /tmp/score6_invsqrt_oneand --seconds 110
/workspace/scratch/7f542e06b7cf/kickmix_venv/bin/python score6_invsqrt_joint_positive.py --out /tmp/score6_invsqrt_positive
```

The certificate uses the system Python with NumPy and SymPy; the native
positive control uses the existing Kickmix environment. No environment was
modified. `score6_invsqrt_manifest.json` hashes the new code, small receipts,
synthetic circuits, incumbent, verifier, and read-only helper dependencies.
Scratch truth tables and bounded solver input files remain in
`/workspace/scratch/3815fb5fae06/score6_invsqrt` and are reproducible from the
pinned KMX.

There is no new full official invsqrt run because this branch produced no
new benchmark candidate. The previous accepted circuit and its complete
official verification remain the deliverable baseline.
