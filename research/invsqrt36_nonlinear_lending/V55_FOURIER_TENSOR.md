# V55 — finite Fourier control tensors and integer angle carry
Research only; NOT SUBMISSION. Parent is PR128's 34Q dictionary, SHA256 63b11abe5df0e59a01c0ddce2020d1b5f93656106518125e26e03339996ebd12. Separate from the competitive 37Q arithmetic oracle. No official verification or score claim.

| native circuit | Q | ops | CCX | generic rotations | HMR |
|---|---:|---:|---:|---:|---:|
| PR128 dictionary34 | 34 | 258639 | 21820 | 5399 | 5340 |
| V55 multioutput tensor | 36 | 173497 | 18903 | 5389 | 5390 |
| V55 integer angle carry | 36 | 211971 | 21613 | 4348 | 6431 |

V55 tensor SHA256 b272cde02a84aa2149e575937560248a28f82b398ee14cfd1063a059feb1241b.
V55 carry SHA256 5ed3cda0d1d26fa761f9a3d2a47bf8b331f62dc903a05bcfe9ea637ae6dc1ded.
Both serialized circuits checked over all 2^22 inputs: independent HMR phase debts zero, rotation controls and input/scratch restoration exact; integer phase modulo 2^64 turns equals the parent on full cube. Exact integer squared tolerance passes all 3133452 legal inputs, observed worst relative-error/tolerance 0.8125815968960524 at x=1792. No rotation synthesis/official verifier.

## Direct finite application
The mutually exclusive dyadic flags P_i and Walsh masks are represented as T[rotation,block,bit] over GF(2). Constant affine terms handled separately. Factor along each of three axes, merge common pairs, explore invertible output shears; exact contraction checked. 122,902 batch candidate trials (sum of six cluster counters), 3,538 selected batches, maximum five target slots in first cluster and four otherwise. Each shared factor AND distributes to several output targets with CX conjugation; measure outputs and settle their independent phase debts. Single-output factor sum 17687 -> 15405 with 3498 flag preparation CCX, final 18903. Exact identical/complement control grouping accounts for nine fewer total rotations; ten fewer generic rotations.

A separate compiler groups 1041 triples of equal coefficient a; integer population sum equals parity + 2 majority. Generate parity and majority simultaneously using one extra CCX and a fourth slot; HMR phase cancellation. Three rotations -> two, exact per-triple packed truth masks and modular phase verified. More CCX than tensor-only candidate, so separate Pareto point; do not add improvements.

An initial phase verification incorrectly compared coefficient representatives after division by 2 modulo 2^64. These are not unique; fixed to compare evaluated modular phase values via integer Walsh butterflies, independently checked native masks and HMR debts. No rejected circuit adopted.

## OpenAI/math scope
Read actual proof modules IntegralTensorBound.lean, IntegralConvolutionTheorem.lean and GridUpper.lean in corcondor/math/lean/OAI/LinearAlgebra/FiniteFourier and prior ExactExponent.lean. See https://github.com/corcondor/math/blob/main/lean/docs/379.md. Integer tensor contractions and division-free arithmetic motivate the implemented finite factor search. No direct claim of implementing the asymptotic n(log n)^(1/2+o(1)) transform algorithm or n^(9/4) matrix multiplication; GF(2) tensor factorization and ordinary integer Walsh butterflies are the actual operations. The source formalizes field hypotheses and a different cost model. 
Independent dyadic master-profile experiment (split=2/3, canonical exponent parity; ordinary Walsh) produced 14,141/15,013 coefficient occurrences; best screened 2-bit master beta=8 gave worst error ratio 0.906802, 5560 global dictionary layers before physical flag allocation. Not compiled; not counted as native gain.
Full executable sources, parent inputs, native outputs and receipts in companion ZIP. Lean local identities only, not full circuit formalization. No main or Kaggle modification. Competitive 36Q oracle remains unresolved.
