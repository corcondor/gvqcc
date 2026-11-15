# DQI e4 interval cuts and a one-pivot GF24 consume

The interval graph refers to the frozen accepted `dqi.kmb` with SHA-256
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.
The GF24 circuit is a native component experiment. There is no new submitted
circuit or measured whole-decoder score in this directory.

## Exact deletion counts on the pinned schedule

Each vertex is a reset-separated wire lifetime. Vertices are adjacent when
they overlap in the instruction order. The graph is an interval graph, so
its largest live set is a maximum clique. Mark every lifetime on a quantum
ABI wire compulsory. Relax the physical problem by allowing a complete
non-ABI lifetime to be deleted at unit cost without requiring replacement of
its stored value or repayment of phase.

The KMB has 58,868,734 operations, 30,420 lifetimes including 840 compulsory
ABI wires, and 1,570 stretches at width 889, totalling 9,679,108 operation
positions. The exact results in the relaxation are:

| Target live width | Minimum complete optional lifetimes to delete |
| ---: | ---: |
| 888 | 3 |
| 887 | 15 |
| 884 | 51 |
| 880 | 99 |
| 872 | 195 |
| 864 | 429 |
| 857 | 4,935 |

At the earliest point at which the bound is exceeded, at least one of the
active optional lifetimes must be removed. Remove the one ending last.
Swapping this choice into an optimal deletion list leaves the processed
prefix feasible and frees capacity for at least as long on the remaining
suffix. The sweep uses two endpoint heaps and costs (O(L\log L)) time and
(O(L)) storage for (L) lifetimes.

The width-888 optimum also has an independently checkable certificate.
These three operation positions each have width 889. No optional lifetime
covers two of them. The three selected lifetimes together cover all 1,570
peak stretches. Indexing is zero-based and intervals are half-open.

| Peak witness | Selected physical wire | Selected lifetime |
| ---: | ---: | --- |
| 17,100,570 | 864 | [17,099,459, 17,119,220) |
| 18,497,205 | 863 | [17,127,041, 54,188,266) |
| 54,192,960 | 875 | [54,180,065, 54,203,660) |

The selected intervals are active data rather than untouched padding.
Wire 864 is created by `CCX 876 875 864`, subsequently controls a CCX on
ABI wire 48, and ends with HMR into classical bit 208167. Wire 875 also
controls a CCX on ABI wire 48 and ends with HMR into bit 208168. These two
lifetimes each appear in 51 operand slots. Wire 863 begins with a CX copy
from wire 840, occurs in 149,062 operand slots including a CCZ shortly before
its witness and a CX shortly after, and ends with HMR into bit 208118.
This exposes two relatively short computed values versus one long-ranging
value with substantial dependencies. A legal split must prove how to
retain or reconstruct the old value and phase across its live gap.
The audit establishes neither a valid split nor a reason that all splits
would fail.

In particular, the Q889→857 proposal would need 4,935 deletions in this
relaxation. A replacement program could instead split, move, or re-encode
lifetimes. The numbers cannot be promoted into width lower bounds for such
programs. The previous score5 interval and branch audits supply extraction
and constant propagation. The new calculation supplies an exact objective and
witnesses for selecting complete intervals on the frozen schedule.

## Dependency cut and phase-safe GF24 pivot

Consider an exact bilinear tensor for field multiplication with rank-one
terms (a_i(x)b_i(y)w_i). For any nonzero linear output functional
(\eta), the right forms (b_i) of terms with (\eta(w_i)=1) span the
complete right dual. Otherwise some nonzero (y) would annihilate all such
forms and hence (\eta(xy)) for every (x). Choose (x=c/y) with
(\eta(c)=1) to obtain a contradiction. Thus a rank-one schedule that delays
all updates to one output projection while retaining the full input domain
keeps a full right-operand information requirement for the delayed terms.
This argument applies to that scheduling model.

A chart allows a different construction. Choose coordinate zero on the
source, output, and right operand, and require source bit zero to equal one.
On this chart the coefficient of the old target bit zero in new target bit
zero equals one, because the zeroth field basis element is the unit. Split
the tensor into terms that read old target bit zero and terms that do not.
Accumulate bits 1–23 of the first group in a clean 23-bit temporary.
Subsequent terms need only old target bits 1–23, so the late group can
directly XOR into the in-place bit zero as well as into the buffer.
The delayed contribution from the early group to bit zero reduces to a
linear parity plus a scalar bilinear form on the other 23 coordinates of
both inputs. Factor its binary matrix at its rank, 22. Swap the other
coordinates, HMR their old values, and store an exact deferred phase mask
with bit zero set to zero. The resulting phase agrees with the standard
closing convention.

| Native component | Extra quantum bits | Static Toffoli-like |
| --- | ---: | ---: |
| Rank-99 reference prefix | 24 | 99 |
| Pivot prefix | 23 | 121 |
| Reference prefix and existing closing | 24 | 459 |
| Pivot prefix and existing closing | 24 | 481 |

All 576 field basis-pair identities were checked. Each exported native KMB
passed 4,096 shots across two measurement seeds for source integrity,
target value, probe integrity, clean scratch and exact phase. The closed
pair includes linear and quadratic phase probes on the product between
compute and uncompute. The pivot chart requires only one source coordinate
to be fixed, covering exactly half the field, unlike the 12 known source
coordinates in the narrower normalized GF24 experiment. The existing
closing still peaks at 24 helper qubits, and this factorization adds 22
Toffoli-like operations. Its applicability to e4 call sites was not
established.

## Reproduction

Run the existing extractor and the new interval and witness calculations
from the repository root. Point the variables at the frozen input and its
matching official source tree.

```bash
g++ -O3 -std=c++17 score5_dqi_width_intervals.cpp -o /tmp/dqi-width-intervals
/tmp/dqi-width-intervals "$DQI_E4_KMB" /tmp/dqi-e4.tsv > /tmp/dqi-e4-raw.json
python graph_dqi/interval_cut.py --tape "$DQI_E4_KMB" \
  --intervals /tmp/dqi-e4.tsv --interval-audit /tmp/dqi-e4-raw.json --out /tmp/dqi-e4-cut.json
python graph_dqi/witness_activity.py --repo . --tape "$DQI_E4_KMB" \
  --cut /tmp/dqi-e4-cut.json --out /tmp/dqi-e4-witness.json
python graph_dqi/one_pivot.py --work "$DQI_CONTROLLER_WORK" --out /tmp/dqi-pivot
```

The last two commands require NumPy. The native component additionally uses
Kickmix and `gf24_nested_norm.py` from the Syed v12 controller work tree.
