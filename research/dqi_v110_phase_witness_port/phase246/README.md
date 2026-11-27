# Exact phase-boundary stress and shared physical pivots (not a submission)

The phase artifact is the SHA-pinned PR #246 tape, reproduced unchanged. Its
input is 35 non-leading padded locator coefficients followed by the 35-word
H frame. The raw 70 syndrome words are NOT accepted by this KMB. The classical
front end here uses PR #248's packed continued fractions and compares every
word of the pre-phase state and the restored syndrome with PR #246's classical
oracle. Compare the independent native expected phase from the packed fixtures,
not a phase calculated from the candidate's output.

The precise correction to the #248 reciprocal schedule is that its series
inversion slice depends on the physical pivot p, not on the pair (i,k)
separately: p=2i+k-1 and its length is 70-p. If j=i+k, p=i+j-1. The next
selected pair starts at j and has endpoint l>j, so its pivot is
j+l-1>p. Sweep physical pivots from 0 to 68, doing one reciprocal per
applicable position. Recover the continuation from the latest selected
boundary. On reverse, unpack first, then use the two latest boundaries to
recover and undo each pivot. Packing and padding are unchanged.

This removes duplicate *static word-level* reciprocal sites: 630 -> 69,
and 335,225 -> 41,956 Frobenius multiply-XOR sites in this part of the
forward reference. No word-level decrease is represented as a Toffoli,
CCX, executed-paid or score decrease. Conditional control synthesis,
packing, the modular arithmetic, and the full native front end and
inverse are still missing. The phase component alone cannot satisfy the
full circuit success criterion.

Reproduction: build both tapes using #246 at
f88814465d71ec05d9585efb78a7da1aca560e8d. Add packed_cf.py from
ef49d50d9582ea401000abb17c482fe3cbf68276 (PR #248).
Run stress_seam.py from that build directory with KickMix 1.0.0 and the two
archived fixture files named by the script. The JSON lists the exact tape
hashes and shot/error counts. PhysicalPivot.lean proves the indexing rules
only, not all reversible semantics or the KMB.
