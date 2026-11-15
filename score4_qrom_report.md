# Score4: functional high/low QROM synthesis

## Outcome

This bounded experiment obtained **no additional CCX reduction**. The submitted
score2 chemistry family remains at **4,033 CCX per pass**. Its NPZ, all angle
words, numerical coefficients, and loader bytes were not changed. No candidate
KMB or new official scoring run was produced. The search is now stopped.

The source NPZ is pinned to
`5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`.
This is the existing 20-word score2 refinement. The newer public 4,030-CCX
family was not available as local input and was not analyzed or claimed as
an improvement from this experiment.

## What was actually implemented

The earlier fixed-feature lower bound and fixed-product dictionary tests were
not repeated. Instead, the new compiler uses the **actual functions** carried
by the prepared wires. They split as a high-address function plus a function
of the four low address bits. The high-only span has dimension 76 on 77 high
addresses; the low-only span has dimension 16 on 16 low addresses. Removing
the shared constant leaves a **75 × 15 × 35** cross tensor.

This differs from treating all 90 prepared inputs as formally independent
Boolean variables. Products of low-only functions are already in the free
linear span. Products of high-only functions need at most one extra quotient
coordinate. The compiler explicitly recovers that missing coordinate; it
does not discard an unimplemented nonlinear correction.

For a fixed output direction, two cross products can be packed as

\[
h_1\ell_1+h_2\ell_2
=(h_1+\ell_2)(h_2+\ell_1)+h_1h_2+\ell_1\ell_2.
\]

The mixed product costs one AND. The two remaining terms are univariate
functions, handled in the checked feature span plus its single missing
high-only direction. Alternative pairings are considered when they can
cancel that one shared correction. X/CX corrections are recovered from exact
1,220-address truth tables.

Two search implementations use this compiler:

1. `score4_qrom_cross_search.cpp` searches joint bilinear decompositions with
   the pinned Polytof BASE implementation. Its objective is the number of
   packed ANDs, not the raw bilinear rank. It permits bounded intermediate
   cost increases and independently checks the entire cross tensor.
2. `score4_qrom_matrix_search.cpp` directly transforms matrix-valued terms.
   Whole matrices of low rank are combined with their output directions,
   allowing an AND pair with the same two-dimensional low-function space to
   be transformed in one step. Every matrix is charged
   `ceil(matrix_rank / 2)`; the complete tensor is checked independently.

An initially considered three-control normalization was **not** counted as a
new method: independent inspection established that Polytof COMM already
uses the equivalence between the factors `a`, `b`, and `a XOR b` modulo
linear terms. That proposal was abandoned before a duplicate search was run.

## Measured work and exact validation

| Search | Batches | Proposed moves | Accepted moves | Time | Core ANDs before / best |
|---|---:|---:|---:|---:|---:|
| Functional bilinear search | 14 | 849,444 | 143,373 | 64.025 s | 2,706 / 2,706 |
| Direct matrix search | 14 | 19,313,442 | 4,275,346 | 70.025 s | 2,706 / 2,706 |

These are finite optimizer trajectories, including neutral and temporarily
more expensive moves. They are not a proof of minimum multiplicative
complexity. Batch 0 is excluded because its accumulation crosses nonlinear
updates of control wires.

The compiler reconstructed all 14 original cross tensors and their exact
full-address Boolean functions with the original core counts: 187, 188,
189, or 212 ANDs. No extra high-only correction was needed for these baseline
reconstructions.

For an independent end-to-end bridge check, batch 4 was actually synthesized
into a circuit and checked with `chemistry_reachable_exact_proof.py`:

- **2,440** address/direction cases: all 1,220 addresses, forward and reverse.
- Every output bit matches the same declared incoming/outgoing batches.
- Selection is restored and scratch is zero.
- All **148 formal HMR outcome variables** across the two checks have zero
  phase coefficient, covering every measurement branch.
- The reconstructed circuit retains **263 CCX and 125 qubits**.

This bridge check concerns the two reachable input subspaces of that batch.
It does not establish an arbitrary-target XOR extension. It is a check of
the compiler, not a passing reduced candidate. The compiler and proof record
are bound by SHA256 in `score4_qrom_manifest.json`.

The first 20-second prototype run exposed a scheduling issue: cloning and
rejecting a proposal could repeat the same internal random state. It was
fixed by drawing the proposed pair from an external optimizer RNG. That
prototype is preserved separately and **excluded from both totals above**.
No verifier seed or salt, circuit-hash scoring, or sampled-test selection was
changed at any point.

## Reproduction

Use the source family as a read-only input, a fresh workspace, and the Python
environment with KickMix and NumPy. For example:

```bash
python score4_qrom_cross.py prepare \
  --loaders /path/to/score2_best_family --batch 4 \
  --workspace /path/to/fresh_score4_workspace

g++ -O3 -std=c++20 -march=native score4_qrom_matrix_search.cpp \
  -o /path/to/fresh_score4_workspace/matrix_search

/path/to/fresh_score4_workspace/matrix_search \
  /path/to/fresh_score4_workspace/input_4.txt \
  /path/to/fresh_score4_workspace/matrix_4.json \
  5 3 20261119 2500
```

The other C++ wrapper uses the unchanged
[Polytof implementation](https://github.com/ZIB-IOL/polytof), commit
`0dcac107d15adc34dc646242d222f21ae7d32699`, compiled with `-D BASE -D VEC_WORDS=2`
and its `src` and `third_party` include paths. Its underlying method is
described in [Tensor Decomposition for Non-Clifford Gate Minimization](https://arxiv.org/abs/2602.15285).

The executable arguments and seeds for every run are recorded in
`score4_qrom_results.json`; raw inputs and outputs are archived in
`score4_qrom_raw_runs.json.gz`. Search stopping is time bounded, so exact
trajectory lengths depend on execution speed. The input construction,
Boolean correction checks, and phase proof are deterministic.

If a future search returns a lower packed count, compile and prove it with:

```bash
python score4_qrom_cross.py build \
  --loaders /path/to/score2_best_family --batch 4 \
  --workspace /path/to/fresh_score4_workspace \
  --terms-json /path/to/fresh_score4_workspace/matrix_4.json
```

The builder writes a KMB only if the final implemented count, including any
missing-high correction, is lower and both reachable phase proofs pass.
