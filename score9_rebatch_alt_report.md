# J=4 alternative variable partitions and exact care-domain completion

## Result

The alternative search did **not produce a production score improvement**.
It screened every 4/7 and 5/6 split whose complete address-function banks fit
the 128-qubit loader cap: **532 partitions × 19 batches = 10,108 circuits**.
The best complete-bank construction remains the natural low bits `{0,1,2,3}`
with **5,197 Toffoli per pass**, using the other chemistry agent's joint
odd-rank sharing identity. J=4 needs at most **4,170** for improvement and
**3,643** to reach the current aggregate score target 28 at fixed physics.

| Construction | Loader Toffoli per pass | Maximum loader qubits | Status |
|---|---:|---:|---|
| Best canonical completion, independent paired outputs | 5,434 | 125 | Estimate, exact ranks |
| Best canonical completion, joint odd full-rank pairs | 5,197 | 125 | Estimate; three representative circuits proved |
| Best exact care completion over all partitions, independent outputs | 5,434 | 125 | Same best partition |
| Best exact care completion plus implemented joint sharing | 5,197 | 125 | Same best partition |
| Best 5/6 split, canonical completion: low `{0,1,2,3,10}` | 8,447 | 128 | Estimate |
| Same 5/6 split, exact minimum-rank completion | 5,651 | 128 | Three representative circuits proved |
| Low `{0,1,6,7,10}`, canonical completion | 8,764 | 128 | Estimate |
| Same split, exact minimum-rank completion | 5,914 | 128 | Three representative circuits proved |

All 19 batches choose the natural low four bits in both global best rows.
The care-domain freedom is substantial for the 5/6 splits containing bit 10,
but it does not overcome their bank and cross-product costs. This closes this
specific construction search; it is **not a lower bound for general quantum
circuits, multi-output tensor rank, nonlinear intermediate functions, or
state-dependent reversible updates**.

## Exact input and scope

The source is `score8_chem_v27_recovered_words.npy`, the words recovered from
the actual current circuits, not the differing `submission.npz` declaration.
The raw `(1220,75)` uint8 array has SHA256
`8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`.
The 75 angles are padded by one zero angle and regrouped into 19 batches of
four. Each loader XORs the current batch with the preceding batch. Coding
bit 7 as bit 7 XOR bit 6 exposes the known low-address tag channel, while the
compiler still handles all 32 output bits without assuming free tag ancillas.

The generated circuits use 11 selection qubits, 32 word qubits, separate
low/high monomial banks, and two temporary linear forms. Bank products are
computed by CCX and erased by HMR followed immediately by the corresponding
classically conditioned CZ. Pure bank functions and arbitrary target fanout
use CNOTs. This is an implementation choice, not a claimed rule restricting
the competition to XOR and AND.

No source circuit or submission was modified. No full official verifier,
Kaggle submission, Git operation, or production artifact replacement was run.

## Care-domain method and its exactness

The legal addresses `0..1219` form a down-set under taking bit subsets.
Therefore a physical monomial with mask at least 1220 vanishes on every legal
address. ANF coefficients with masks below 1220 are fixed by the requested
table; the remaining coefficients are genuinely unconstrained. The first
screen sets them to zero, rather than imposing the old artificial 1232-row
extension.

For any bit partition, the cross-coefficient matrix has a staircase of known
entries. In ascending high-mask order, the known low-mask rows form a
nonincreasing prefix. The minimum rank for one output can consequently be
constructed exactly:

1. Project the earlier independent columns onto the current known prefix.
2. If their span contains the new prescribed prefix, extend the new column as
   the corresponding full linear combination, adding no rank.
3. Otherwise a rank increase is unavoidable. Add the prescribed column with
   a zero unknown suffix.

The choice in step 3 loses no future completion: every future prescribed
prefix is contained in the current one, so the currently unknown suffix is
never constrained later. Likewise, the projections of all preceding columns
onto the current prefix are already fixed by the input, irrespective of
earlier completion choices. Each detected increment is therefore necessary,
and the construction attains their sum. The guarantee concerns each output
matrix separately. The implemented joint sharing can then reduce the sum of
paired-product counts, but no optimality is claimed for that joint step.

The screen also records the weaker bound obtained by deleting all partial
columns. For some 5/6 splits that bound becomes the bank cost alone (1,577
over the family). It is explicitly **not used as an attainable cost**.

## Validation

`score9_rebatch_alt_verify.py` independently enumerated all 512 full 3×3
binary matrices for each of the 20 nested care patterns. Across 10,240 full
matrix enumerations and 1,395 distinct partial matrices, the completion
algorithm always attained the brute-force minimum rank. It also compared the
separate C++ estimator against the Python factorization/compiler on 24 actual
partition/batch combinations, 32 output matrices each. All ranks and predicted
gate counts matched.

Nine representative KMB circuits were emitted and symbolically proved:

| Low bits | Batch 0 | Batch 5 | Batch 18 | Q | HMR variables cancelled per circuit |
|---|---:|---:|---:|---:|---:|
| `{0,1,2,3}` | 290 | 268 | 268 | 125 | 80 |
| `{0,1,2,3,10}` with optimal care completion | 307 | 295 | 295 | 128 | 83 |
| `{0,1,6,7,10}` with optimal care completion | 314 | 309 | 314 | 128 | 83 |

Every proof covers all 1,220 legal addresses, arbitrary values of all 32
target bits, unchanged selection bits, all scratch qubits restored to zero,
and exact cancellation of every symbolic HMR phase variable. Consequently
the same circuit implements its required reverse transition as well. The
proof reuses the established arbitrary-target checker from
`outcome_chem_j4_synthesize.py`; the new compiler and estimator are separate
implementations. These nine circuits are proof fixtures, not a proposed
submission family.

## Reproduction

Run from `/workspace/scratch/7f542e06b7cf/gvqcc_repo` with
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python`:

```bash
python score9_rebatch_alt_partitions.py
python score9_rebatch_alt_compile.py
python score9_rebatch_alt_compile.py --completion --partition 1039 --batches 0 5 18 --out /workspace/scratch/3815fb5fae06/score9_rebatch_alt/care1039
python score9_rebatch_alt_compile.py --completion --partition 1219 --batches 0 5 18 --out /workspace/scratch/3815fb5fae06/score9_rebatch_alt/care1219
python score9_rebatch_alt_verify.py
```

The first command compiles the C++ estimator with `g++ -O3 -std=c++17`.
The default output directory is
`/workspace/scratch/3815fb5fae06/score9_rebatch_alt`.
It contains `partitions.csv`, `partitions.json`, coefficient data,
`verification.json`, proof records, and KMB fixtures. The screen took about
10 seconds; no long-running search remains active.
