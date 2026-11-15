# Exact classical gauge selection by sorting

## Result and scope

`score3_gauge_sort.py` computes the exact most frequent label among 4,025
twelve-bit classical residual masks and one virtual zero. It chooses the
least numerical label on ties. Its standalone native tests pass, including
input preservation, zeroed scratch, and unchanged phase. The completed
official full-decoder run also passes: **102,400 shots, zero value errors,
and zero phase errors**, with the official default seed and confidence.

The selector has **12,336,839 classical instructions, zero quantum qubits,
and zero Toffoli-like operations**. The fixed-128 selector has 12,887,775
instructions; the earlier fixed-128 plus 32 observed candidates selector has
20,197,186. This is an exact full-label selector with fewer classical
instructions than either of those implementations. It uses 53,288 temporary
classical bits, of which only the twelve-bit label remains live on return.

## Comparison and exchange

Let `a`, `b`, and `g` be classical bits, and let `d = a XOR b`. The sequence

1. `b ^= a`, so `b` holds `d`;
2. `g ^= a`;
3. clear `g` conditionally on `b`;
4. `g ^= a`

leaves `g` unchanged when `d=0` and sets `g=a` when `d=1`. Applying this from
the least significant bit to the most significant bit, starting at `g=0`,
therefore gives the unsigned comparison `g = (left > right)`. The last
differing bit is the most significant differing bit. This is a classical
overwrite: these wires are `km.b`, never `km.q`.

At this point each right word bit holds `d=a XOR b`. Conditionally XORing
`d` into the left bit and then unconditionally XORing the left bit into the
right bit gives

\[
 a'=a\oplus gd,\qquad b'=d\oplus a'.
\]

For `g=0` this restores `(a,b)`; for `g=1` it produces `(b,a)`. Each comparison
therefore sorts two words ascending. The implementation takes
`4w + w + w + 3 = 6w+3` instructions for width `w`, including clearing `g`
at entry and the condition-stack push/pop. For thirteen-bit words this is
**81 instructions**. `g` can remain at its comparison result because the
next comparison resets it; the complete selector clears it before return.

The counter comparison restores the right word immediately after each bit,
using five instructions per bit. It therefore leaves both compared counters
unchanged.

## Sorting and padding

The implementation uses the recursive odd-even merging network introduced
by K. E. Batcher, *Sorting networks and their applications*, AFIPS Spring
Joint Computer Conference (1968), pages 307–314:
<https://doi.org/10.1145/1468075.1468121>.

Each sorting call sorts its two halves and recursively merges the odd and
even subsequences, followed by the interior adjacent comparisons of the
odd-even merge. All comparators are ascending. The emitted 4,096-input
network has **139,263 comparators**, hence **11,280,303 sorting instructions**.
These counts are checked directly against emitted instructions.

The original 4,025 masks are used only as classical controls when making
private copies. The copies are thirteen bits wide. One extra copy is zero;
the remaining seventy copies are the integer sentinel 4,096. All legitimate
labels are below this sentinel. Consequently, after sorting, the first
4,026 entries are exactly the legitimate input multiset including the
virtual pivot. The seventy sentinel entries are never scanned for the mode.

## Exact run counting and tie handling

The first sorted legitimate word is zero because of the virtual pivot.
The current count and best count start at one and the best label starts at
zero. For each later legitimate word, the code resets the run count if the
word differs from its predecessor, then increments the count exactly.
The largest reachable count is 4,026, which fits in twelve bits.

The best label is replaced only when the current run count is strictly
larger than the best count. Updating at every prefix of every run has the
same final result as comparing completed runs: whenever a later run exceeds
the incumbent, it replaces it, and it retains the same label as that run
continues. A tie never replaces the incumbent. Since labels are scanned in
ascending order, ties retain the least label. The final run is handled by
the same update, so no separate terminal flush is required.

The run-count stage takes **901,602 instructions**. Initialization, copying,
and clearing account for the remaining 154,934 instructions.

## Pointwise scan-cost statement

For any input masks, define

\[
 n(\ell)=\mathbf1[\ell=0]+\sum_{i=1}^{4025}\mathbf1[m_i=\ell].
\]

The selector returns a label attaining `max_l n(l)`. Every label returned by
an earlier restricted or capped selector is among these 4,096 labels.
Therefore the exact number of zero scan masks can never decrease on any
input. This statement is deterministic; it does not depend on a random
seed, a distributional approximation, or a sampled average.

The existing scan uses eleven Toffolis for each nonzero candidate mask.
Thus the pointwise scan saving is eleven times the increase in zero-mask
count. This does not by itself certify a complete decoder's value/phase or
an official measured average Toffoli count.

## Integration boundary

The build starts from the pinned `e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`
480-CCX/gauge128 baseline. It checks the complete old gauge prefix and suffix
instruction columns against the reference pieces before replacing either.
The decoder body is copied byte for byte.

The selected label is copied into the same fixed pivot. All twelve bits
are XORed into the normalized residual masks. The existing field geometry
then applies the corresponding syndrome compensation using all twelve label
bits. This is the same full-width phase-compensation construction used in
`dqi_gauge_dynamic.py`, including 2,126 classical-controlled CZ operations.
The closing suffix reverses the full-width shifts, inverts mask scaling,
clears the pivot, and closes the original gauge. The selector's private
classical work has already been cleared and freed.

## Native evidence

The final 81-instruction comparator passes 8,656 native pairs: exhaustive
four-bit values, every single-bit boundary through bit twelve, and sentinel
4,096 against each of the 4,096 legitimate values in both orders. The
native network tests exhaust every binary input for sizes 2, 4, 8, and 16.
The exact counter increment is checked on every one of its 4,096 states,
including wraparound; wraparound is outside the selector's reachable count
range.

The complete 4,025-mask selector is checked on 100 cases including constant
inputs, equal-frequency winners, counts around powers of two, ascending and
descending inputs, and 64 fixed-seed random inputs. Every selected label
agrees with an independent Python `Counter` oracle. All original mask bits
are preserved, all private work bits are cleared, and phase is unchanged.
The seed is only a reproducible test fixture seed: circuit construction
contains no seed or input-distribution choice.

The primitive tests plus the comparator/run invariants above qualify the
implementation. The small-network exhaustive checks are not claimed as an
exhaustive test of all 4,096-word inputs. Complete official decoder testing
was performed separately by the integrating caller, as recorded below.

## Completed official decoder verification

`score3_dqi_full_verification.json` is a byte-for-byte copy of the integrating
caller's full official receipt. It binds circuit SHA256
`9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1`
to verifier SHA256
`f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`.

| Official result | Value |
|---|---:|
| Status | PASS |
| Verified shots | 102,400 |
| Value errors | 0 |
| Phase errors | 0 |
| Mean Toffoli count | 382,095.68779296876 |
| Maximum Toffoli count | 382,934 |
| Quantum qubits | 889 |
| Operations | 58,869,042 |
| Repetition factor | 1.1912604648115832 |
| Official component cost | 359,734,745,778.9876 |

The run uses `seed=null`, empty salt, and `log2_delta=-128.0`; its stated
scope is the full competition verifier defaults. It is an actual official
component result. No public leaderboard result is implied. Native and build
receipts remain unchanged and separately hash-bound in the gauge manifest.
