# V115 — DQI total-correctness audit (NOT SUBMISSION)

This replaces the *reference mathematical algorithm*, not an existing native
KMB. The old native circuit must not be promoted. No Kaggle action, main
merge, or score improvement is claimed.

## Audit
Relevant history includes #1, #2, #5, #12, #13, #155, #165, #166, #171, #173,
#181 and V112/V113/V114 replay bundles. Local circuit equivalence does not
imply agreement with the independent decoding specification.

The ordinary finite-chart update is impossible if N mod g = 0 and D mod g
is nonzero. Keeping an explicit zero tag restores reversibility but can
overflow the final degree budget. Omitting a zero tag merely because h=0
is also unsound unless the input denominator is a unit at that node.

## V115 adaptive reference
For m remaining slots assume deg N <= m, deg D <= m+1, gcd(N,D)=1, and at
most two occurrences of each irreducible quadratic. Use a nonzero finite
pivot when one exists. If all residues vanish and N is nonzero, the product
of the distinct quadratics divides N. Its degree is at least m, hence
deg N = m. Euclidean division D=qN+R then has deg q <= 1 and deg R < m.
Store the pivot kind, actual node/slot and head explicitly, and use the
corresponding inverse. If N is zero, the coprime denominator is a nonzero
constant and the step is identity. Each step consumes one slot.
The terminal pair satisfies deg N <= 0, deg D <= 1, not necessarily N=0.

The adaptive reference assumes access to the full polynomial pair. The
finite-node schedule, infinity handling, tags, reverse path, syndrome and
HMR semantics still have to be compiled and linked to the real KMB. In
particular, 34 slots is not a claim about physical qubit width or cost.

## Independent decoder and acceptance contract
Two syndrome-only decoders (BM and EEA) independently reconstruct errors.
Each rejects unless its sparse output has at most 35 nonzero values and
recreates all 70 syndromes. Two such error vectors have a union of support
of size <=70, so Vandermonde injectivity guarantees uniqueness.
The Lean source formalizes the abstract chart conditions, local and trace
inverse, sparse-moment uniqueness, certified phase, and degree budgets.
The concrete product-divisibility hypothesis and physical circuit semantics
are not discharged by these abstract theorems. A source file without sorry
is not itself proof of successful compilation.

## Local classical regression
Run `python regression.py` (Python standard library).
Expected local receipt: 405/405 exact adaptive roundtrips, tail bound and
independent BM/EEA; 25 forced-one poles, 20 simultaneous all-node poles,
360 weight-stratified inputs; 25 fixed-zero tail overflows; 20 infinity cases.
No competition fixtures or secret salts are included. The native replay
is separate from this synthetic regression.

## Promotion gate
No submission until the actual circuit has independently proved/checked
syndrome restoration, all workspace cleanup, and phase for the legal
domain, passes adversarial poles and weights 0–35, and passes both official
salt runs with zero errors. Check the exact KMB hash and score costs.
Lean Actions must succeed and print axiom dependencies. No automatic
promotion even if the abstract proofs and classical regression pass.
