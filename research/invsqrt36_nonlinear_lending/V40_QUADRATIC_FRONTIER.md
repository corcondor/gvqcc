# V40 — PR94 direct replay and nonlinear observation-frontier projection

Research-only, NOT SUBMISSION. Parent PR94 SHA256 2a4689fc1316ff43ff61002149e2a9e6f9b54239ba4e9c121f282423a17aeabd. No main merge or Kaggle changes.

## Native results (independent serialized BDD replay PASS)
| track | ops | expected paid | static paid | full cuts | HMR |
| --- | ---: | ---: | ---: | ---: | ---: |
| PR94 | 41935 | 23127/16 | 1597 | 3239 | 1276 |
| V40 affine reset | 41945 | 23095/16 | 1595 | 3239 | 1278 |
| V40 compact zero-budget | 41950 | 23095/16 | 1595 | 3149 | 1278 |
| V40 width-budget alternative | 41959 | 23223/16 | 1603 | 3129 | 1278 |

All native circuits remain 37Q. Exact legal domain 3,133,452. Reset screening 60 sites/82 alternatives, accepted two, actual indices 262 (t=q32, a=q15, b=q21, residual q15) and 34413 (t=q25, a=q31, b=q27, residual q19 XOR q29). Independent 41935 aligned checkpoints. New reset parent SHA c401af97020f9cfefd5f99f109fa15dc236d4747dc8bd40cc516199369818e64. Advancing original HMR events: 7609 backward steps,43 proposals/39 exact accepted; budget-zero 22 disjoint edits/90 full-cut relief. Compact output SHA 114ada6431e2342617685d4e663b225ee211ff1a3e55974114fb3d951f8d63fe; 41812 checkpoints. Alternative +8 E,23 disjoint edits/110 full-cut relief, SHA 67506fabbdbfc3c87228ef5b94d0262f07581899c36689c25b061504a7ef95ea; 41780 checkpoints. Different variants, do not sum improvements. Original E1406.3125 not beaten. These are known reset and measurement-adjoint rules re-executed on the new parent, not a new general MBU algorithm.

## New temporal-debt search
Allow locally unrepresentable omitted-coordinate phase reads to accumulate, then settle combined debt with one or two free diagonal atoms at different scope-free cuts. Both early-HMR and unguarded atoms included. 67832 reverse steps,9368 debt-bearing steps,2637 candidate endpoints,26933386 sampled settlement atoms. Two candidates [23196,23204), [23197,23204) pass sampled settlement but exact BDD phase fails (data/rotation/classical/guard match), neither adopted. No claim of global infeasibility. Revisit by exact counterexample-driven guard-sensitive phase dictionary.

## New full quadratic kernel at abstract frontier
Regenerated PR94 XAG with Adaptive window32/flip449, history specialization {794}, first 38 rotation roots; exact packed evaluation equals archived observation graph over all 3,133,452 inputs. Both graphs have 743 ancestor AND atoms, formal observation peak37 at nodes454 and633 only. The history specialization is an observation-graph diagnostic, not postselection; does not represent the full native oracle or its remaining rotations and input restoration.

For each rank37 basis, evaluate all 704 constant/linear/quadratic columns on 3072 fixed sampled rows. Rank680, kernel24 at both nodes. Solve linear incidence constraints requiring coefficient of omitted coordinate f_q =1 and no quadratic monomial involving f_q; exact evaluate each resulting formula on all legal rows. Node454 5 exact decoders, node633 8, zero rejects (13 distinct node-coordinate pairs). Sample kernel rank is not an exact rank claim. Two representative factorizations (0-based frontier basis indices, NOT physical q indices):
- 454: f0 = (f14 XOR f34)*(f16 XOR f20) XOR f1 XOR f5 XOR f14 XOR f20 XOR f35.
- 633: f0 = (f14 XOR f16)*(f20 XOR f34) XOR f1 XOR f4 XOR f6 XOR f8 XOR f14 XOR f20 XOR f34.
Both exact full-domain factorization checks PASS. Each projection onto other 36 basis coordinates is injective on that frontier's reachable graph. Not a physical 36Q synthesis: the two cuts are in a fixed-history observation XAG, original inputs/phase debt and remaining roots must be accounted for.

Cross-frontier transport exact full truth tables: each affine span incl constant rank38; joint rank64, intersection dim12 incl constant (11 mod constant). Products distinct and noncomplementary, neither product in other affine span. Both factors of 454 belong to 633 affine span: u454 = f20(633) XOR f34(633) XOR f36(633), v454 = f16(633) XOR f34(633). Of 633 factors, y633=f20 XOR f34 equals f14(454), x633 not in 454 affine span. Thus transport factors instead of blindly storing products, but no paid saving or native carry-chain implementation follows from these equalities alone.

## Literature and implementation scope
Meuli et al. ROS, https://msoeken.github.io/papers/2019_qpl_1.pdf: XAG/LUT decomposition and memory management; not full LUT mapper/pebbling implementation. Amy & Lunderville, https://doi.org/10.1145/3704873: nonlinear relational domains and phase folding; new temporal debt dictionary and quadratic kernel implemented using packed legal-state evaluation rather than their full Groebner/sum-over-paths framework. Paradis et al. Reqomp https://doi.org/10.22331/q-2024-02-19-1258: width/cost constrained uncomputation; use cost-bounded nonoverlap selection, not full graph pebbling implementation. Zhang et al. divide-and-conquer pebbling https://doi.org/10.1109/TCAD.2025.3570608: article abstract confirms qubit/gate tradeoff; no port of complete Qiskit synthesizer. SAT-Embed-Q https://www.mdpi.com/2624-960X/8/4/111: limited-care synthesis and exact verification; direct binary linear solve for incidence constraints, no SAT engine imported. Khattar et al. https://arxiv.org/abs/2610.23832: competition verification scope. No exhaustive novelty claim; historical ANGLE archive audit incomplete.

Lean proves generic Boolean factor identities, projection injectivity, quadratic sign and finite phase telescope, and arithmetic bookkeeping. Native and frontier reachable premises checked separately in Python. Full circuit Lean proof and competitive full 36Q not achieved. Companion archive includes actual Python generators, verified native parents and outputs, receipts, dependency engines and exact reproduction instructions. No official verification.
