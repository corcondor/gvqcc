# Score7 chemistry: shared-control and phase-gadget investigation

## Result

No chemistry circuit was changed, and no score improvement is claimed.
The actual fifteen retained loaders contain **4033 CCX**, **1115 HMR**, and
**1115 classically conditioned CZ** gates. They contain **zero CCZ** and
**zero Z_POW** instructions. The unchanged candidate remains the score6 family
whose NPZ SHA256 is
`16ee9ad3716309385aa9ce48c1f714e59484b79126ac6fe60591d3ba8bd7ebcf`.

The new implementation screens local joint resynthesis using the complete
reachable forward/reverse word context, including incoming angle words as
possible nonlinear controls. Every one of **19,940 consecutive windows of
2–6 CCX gates** needs at least its original number of new Boolean product
dimensions. Thus none can be replaced by one fewer Toffoli-like gate while
preserving the same complete quantum-wire values at those boundaries in the
basis-preserving XOR/AND model. This is a local lower bound, not a claim that
4033 is globally optimal.

## Relation to the proposed phase methods

The source verifier explicitly rejects `Z_POW` in ANGLE circuits; see
`official_sources/Inzainos/verifiers/dfthcsos/scoreinfra/circuits.py`,
`_reject_rotations`. Its resource counter counts CCX, CCZ and CSWAP as Toffoli-like
operations. A classically conditioned CZ is not charged as a Toffoli. Therefore
substituting a Clifford+T decomposition with six T gates is not an accepted
ANGLE rewrite under this interface, nor does six T directly mean six units of
the competition tariff. The user-proposed paper itself is reviewed separately
by the root agent; no new claim about its construction is made here.

The current loaders already exploit measurement-based erasure. If an ancilla
stores `f(a)=u(a)v(a)`, an HMR outcome m contributes `(-1)^(m f(a))`;
the following conditional CZ on u,v cancels precisely that phase. Its erasure
therefore consumes no additional CCX. The checker follows every formal HMR
outcome independently and establishes cancellation before the single classical
bit is reused. This covers all measurement records, not a random sample.

Fourteen loaders place every such phase correction after their last CCX.
Loader 0 has two intermediate HMR boundaries: these were included in the final
window screen. Across the full family there are no explicit quantum CCZ blocks
to replace directly with a CCCZ decomposition. A high algebraic degree in an
ancilla's address function does not by itself create a charged CCZ instruction.

## New algorithm and precise bound

For each loader k, concatenate the 1220 previous-batch inputs and the 1220
current-batch inputs. Each live wire is represented by a **2440-bit exact truth
table**. The initial incoming words are the actual declared arrays; they are
not replaced by independent arbitrary bits. Constants, all address bits,
all angle-word bits, and all live scratch wires enter the linear span.

At a window entrance define

\[
V=\operatorname{span}_{\mathbb F_2}\{1,f_0,\ldots,f_{Q-1}\}.
\]

For the corresponding exit functions g, calculate

\[
d=\dim\operatorname{span}(V,g_0,\ldots,g_{Q-1})-\dim V.
\]

X, CX and SWAP introduce no new function outside the accumulated linear span.
One CCX introduces at most one, namely a product of its two control functions.
A CSWAP likewise introduces at most one, `a*(b XOR c)`, which is XORed into two
targets. Phase-only gates change no wire values. Clean extra ancillas introduce
only zero functions. Consequently any circuit in this model implementing the
same boundary mapping needs at least d charged nonlinear gates.

For HMR, its outcomes are independent fair branch variables on these
basis-valued functions. Conditioning on the all-zero outcome record gives the
same necessary value lower bound: reset removes a wire function, and diagonal
corrections cannot supply a new one. A valid rewrite must additionally satisfy
the phase contract in every branch. The bound never treats passing a value
check as a proof of phase correctness.

For every tested size n, **d=n**:

| Consecutive CCX count n | Windows checked | Windows with d=n | Windows crossing HMR |
|---:|---:|---:|---:|
| 2 | 4018 | 4018 | 2 |
| 3 | 4003 | 4003 | 4 |
| 4 | 3988 | 3988 | 6 |
| 5 | 3973 | 3973 | 8 |
| 6 | 3958 | 3958 | 10 |
| Total | **19,940** | **19,940** | **30** |

The implementation also checks all 36,600 declared address/direction/loader
transitions, scratch cleanup, preserved selection registers, and cancellation
of all formal HMR phase coefficients. These are inexpensive exact truth-table
checks, not a rerun of the unchanged 78,080-shot official verifier.

Positive and negative controls check two independent products (bound 2) and the
genuinely reducible common-factor identity
`ab XOR ac = a*(b XOR c)` (bound 1), over all 16 four-variable inputs.
The screen therefore does not reject every two-CCX input by construction.

## Distinction from the earlier searches

The earlier prefix-feature rank bound kept the existing control dictionary
fixed. The earlier affine scan examined replacement of one CCX by X/CX gates.
This new bound allows arbitrary new product inputs constructed from **all
current data and scratch functions**, and jointly considers up to six CCX.
It rules out a larger family of local Boolean resyntheses without relying on a
particular XAG heuristic or a random search budget.

It does not rule out wider block changes, a different encoding at a boundary,
different angle words, global rearrangement across windows, or unrestricted
quantum circuits with Hadamards. The boundary is the complete current wire
mapping; a rearchitecture that changes this interface requires another proof.
The exact rank bound is useful for avoiding repeated local solver searches,
but creates no circuit saving by itself.

## Runtime and reproduction

The final scan took **7.675 seconds**, with **35.79 MiB** peak RSS. The script
and final JSON bind the exact input NPZ and all fifteen KMB hashes. No external
submission or candidate KMB was emitted.

```bash
kickmix_venv/bin/python score7_chem_window_rank.py \
  --loaders /workspace/scratch/3815fb5fae06/score2_best_family \
  --table /workspace/scratch/3815fb5fae06/score6_chem/transfer_full/submission.npz \
  --output /new/output/score7_chem_window_rank_measurements.json \
  --max-window 6
```

The final result is `score7_chem_window_rank_measurements.json`.
The earlier measurement-excluding diagnostic was moved out of the source
directory and is not a deliverable or the basis of the final totals.
