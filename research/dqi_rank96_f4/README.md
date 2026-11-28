# GF(4) rank-32 route, exact all-site admission adapter

Research only. Target is exact #323/#325 full native baseline
54817e9385f24940585f5a391025152d4a65a36381887ca77b7bab61413ea2ec,
900Q, static317994, matched1024 mean316094.000.
The previous #323 all333 rank99 integration succeeds; this new branch
does NOT create a new lower-paid full tape. Do not merge or submit.

New approach: recover an actual GF(4)-algebra isomorphism for both
normalized #311 tensors. The coefficient of θ^12 is 9399253 for the
field type, 4385 for the dual-number type in packed F4 coordinates.
Find the unit, β satisfying β²+β+1=0, and a cyclic 12-word basis
with rank24 over F2. Check all576 multiplication basis coefficients.
Construct 33 GF4-product CRT decomposition with 5 rational places
(including infinity), six irreducible quadratic places, two cubic
places, and a separate 33-product seed recovered from the actual
GF16 99-term tower dictionary in #311. Exactly check 576 products
per grouped triple and all resulting tensor coefficients.

Search in the 12×12×12 tensor over F4, rather than the earlier
24×24×24 binary tensor. Nontrivial scalar flip (λ in F4*), shared
factor Gaussian pooling, compound split, and three-term dependent
output rank-one completion. Rank increases up to49 are permitted.
Two types ×200000 initial + two ×180000 triple + two ×250000
tower search = 1,260,000 proposals. Best33 throughout. Rank32 would
expand to 96 CCX (999 static saving on all333); not achieved.

certify.py converts each GF4 product into three binary products,
transports both input covectors and all output weights through exact
isomorphisms, checks all 576 coefficients per normalized tensor, and
generates 72Q native XOR-accumulate gates with dirty-target preservation.
It rejects all present witnesses for strict <=97 admission. Whole #323
compiler must perform its own all333 exact physical ANF checks and
matched full replay before adopting any future certificate.

The exact all333 KMB and #323 source archive were materialized from
Library, but the local execution service returned ClientError on
multiple attempts including Python and container shell. GitHub CI
runs the new exact component admission; no new physical full-tape
run in this branch. Preserve the low-cost complete baseline, not the
533k research comparator. Known saved/dense errors are not repaired.
No score or submission claim.

Background: Rambaud (WAIFI 2014), Ballet et al. (arXiv:1906.07456),
Cenk and Özbudak (J. Complexity 26, 2010).
