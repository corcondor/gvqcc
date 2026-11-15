# Controlled-affine DQI window audit

The input is the exact DQI member of the 27.3278449921 local portfolio.
Its SHA-256 is
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.
The original official cost is 359707293756.04297, at Q889 and mean
382066.52936523437 paid gates with zero failures in 102,400 shots.

The scanner transports a single selected input bit as a linear functional
through the reversible linear operations. At every paid CCX or CSWAP, the
selector must be on one of the relevant control lines, with possible affine
complement. For each complete window it fixes the selector in turn to 0 and 1
and calculates the exact affine map on all other independent bits. The rank
of the difference of the two linear maps is the rank of the relative map
minus the identity. Both conditional translations are accounted for as
affine constants. The common selector can finish on another wire.

If this rank is lower than the paid count, the relative linear map can use
that many transvections, controlled by the selector. To see the count, let
the relative map be A with fixed subspace K. For x outside K, take
v = Ax + x. A covector vanishing on K and v and equal to 1 at x exists
because Ax cannot lie in K. The corresponding transvection fixes K and
maps x to Ax. Composing its inverse with A grows the fixed subspace by one.
Repeat to obtain exactly rank(A - I) factors. Each controlled transvection
is one CCX conjugated by linear Clifford operations. The affine translations
add only Clifford gates. This argument concerns these windows and the
controlled-linear synthesis model.

The actual scan processed 58,868,734 instructions and all 363,654 CCX plus
12,240 CSWAP. It found 566 shared-selector multigate windows, with up to 204
paid gates. No window had a lower relative rank. Measurements, phase gates,
classical condition boundaries and unrelated nonlinear controls are barriers.
The window size cap is 16,384. The result neither constructs a new KMB nor
proves optimality under other arithmetic decompositions. The scored
portfolio keeps the pinned e4 member.

Six KMB fixtures check positive and negative cases, including a physically
moved selector, a mixed CCX/CSWAP rank-zero identity and a phase barrier.

```sh
g++ -O3 -std=c++17 -Wall -Wextra -Werror controlled_linear_scan.cpp -o controlled_linear_scan
python check_controlled_linear.py ./controlled_linear_scan fixture_receipt.json
./controlled_linear_scan "$DQI_E4_KMB" controlled_linear_hits.tsv > controlled_linear.json
```
