# Rolling flag reconstruction: bounded counterexample results

**Four simple decoder families were refuted.** The screen stopped after 25 admitted physical inputs and 425 observed node states: 0.980 seconds, 38,400 KiB maximum RSS. No circuit, worker, frozen reference or verifier was modified. No native circuit simulation was run.

## Method and exact scope

`dqi_rolling_flag_screen.py` uses the existing pure-Python `physical_boundary_oracle.boundary` to rebuild the heads, raw residues and flags from physical roots and nonzero magnitudes. It independently checks the classifier's admitted domain at extractor cutoff 18. The first-three-chart `boundary_scale_first3.changed_carry` reference is observed through `sys.settrace`; its code and state are unchanged. Each observation is after the reference's exact head/flag assertions, at `carry = numerator`, so `head` and `carry` mean the post-update 24-bit head and selected nonzero carry.

The source corpus is the existing, hash-recorded 783-case `first3-full/fixtures.json`. Eligible inputs are processed in a deterministic order across weights. These are **curated physical counterexamples, not independent DQI-law samples**. No failure probability is estimated.

The four candidate families were specified before execution. Every lookup key includes the public node, and Gaussian elimination uses a separate basis for every node. Thus **the experiment allows a different decoder at each public node**; none of the contradictions relies on mixing stages.

## Concrete counterexamples

| Candidate observations available to the decoder | Same public node | First input `(weight, head, carry, flag)` | Second input |
|---|---:|---|---|
| Whole-word zero tests | 33 | `(32, 0, 0xbae154, 0)` | `(33, 0, 0xc9915b, 1)` |
| Zero tests of all four 12-bit halves | 33 | Same pair | Same pair |
| Four half-zero tests, plus each half's least-significant bit and bit parity | 32 | `(31, 0, 0x16ce85, 0)` | `(28, 0, 0xf68caf, 1)` |

Each pair has identical permitted observations and different required flags. Therefore no function of only those observations can recover the flag correctly on both admitted inputs. Full physical roots and magnitudes, fixture identifiers, and numerical observation vectors are retained in `dqi_rolling_flag_screen_results.json`.

## Stronger affine-family contradiction

The fourth candidate allows **any affine GF(2) expression of all 48 head/carry bits and the four half-zero predicates**, with independently chosen coefficients at each public node. At node 34, the following six admitted input states contradict every such expression:

| Input weight | Head | Carry | Required flag |
|---:|---:|---:|---:|
| 30 | 0 | `0x8cd363` | 1 |
| 29 | 0 | `0x261359` | 0 |
| 19 | 0 | `0x306902` | 0 |
| 34 | 0 | `0x898d3e` | 1 |
| 31 | 0 | `0x37aade` | 0 |
| 26 | 0 | `0x248ed8` | 1 |

The six carry words XOR to zero; every head is zero. Both carry halves are nonzero in every row, so the half-zero predicate vectors also XOR to zero. There are six rows, so an affine constant cancels as well. Yet the required flags XOR to one. Taking the XOR of these six equations would require `0 = 1`.

This certificate was also recomputed independently from the saved JSON. It excludes an affine parity decoder **at node 34 itself**, even when other nodes use different formulas.

## What this does and does not settle

The proposed easy reconstruction from current head/carry zero tests or parities does not work. Allocating less workspace based on any of those four hypotheses would fail on concrete admitted inputs, so this line is stopped without emitting or testing a replacement circuit.

This does **not** rule out a nonlinear invariant, information in other registers, a different observation boundary, or a redesigned schedule. It does not establish that 889 qubits is optimal. The screen concerns the exact current source lineage's scalar boundary; it is not another official full-circuit verification of 821 or the optimized candidate.

Reproduction:

```bash
python gvqcc_repo/dqi_rolling_flag_screen.py \
  --output gvqcc_repo/dqi_rolling_flag_screen_results.json \
  --seconds 118 --max-trajectories 20000
```

The process applies a 1 GiB address-space limit and a 118-second wall timer. The saved report records the script and frozen reference hashes, all counterexamples and the exact stop reason. The limit was not approached.
