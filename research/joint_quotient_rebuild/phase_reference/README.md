# Reuse of existing DQI phase/guard mathematics — research only

**Rejected for submission.** This is a concrete patch on the user's 62,086,097-op 900Q / 318,584-static-paid 316k tape, SHA256 2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60. It is not the 4b572141... 69M-op variant. No new proof system or seed/salt selection. Reuse #209 AffinePadding/BranchCollision (moment uniqueness and classical phase repayment), #227 zero-syndrome witness, #229 affine and product-atom transport, and the upstream division.py::zero_flag / phase_zero construction.

The classical shadow executes the same gate semantics on the *zero* syndrome with the actual mask bits and HMR outcomes, accumulating the reference sign in an extra classical bit P. All actual quantum data gates and HMRs are retained; no syndrome is measured or exposed to a classical branch. At the end, repay the reference sign only on the zero-syndrome chart. For legal nonzero errors of weight w<=35, S_j=sum_i e_i x_i^j, j=1..35. If these moments are all zero, the first w rows give an invertible Vandermonde times diag(x_i), contradicting nonzero e_i. Hence only 420 syndrome bits are necessary for the guard on a correctly restored legal syndrome. This reduces the added static paid cost from 1622 (840-bit guard) to 782. The guard uses the old clean work wires at the end, so Q remains 900. Output guard is NOT a repair for an incorrect restored syndrome. The reference shadow uses actual classical SSA states, repeated product atoms and conservative rebases; the independent bit replay is not a full formal proof of the compiler. The abstract end state still has 840 unknown reference data coordinates; zero restoration on every history is not proved.

## Full KMB and verification
- Original SHA above; optimized reference candidate SHA256 2d1ec613eb13a5a37ba1f868ccd7182fa793a5f4868221ddc7a07f85bd9ce442.
- Q=900; B=692769; static paid=319366; 121342788 ops. Conservative affine rebase and condition-scope fusion reduce the unoptimized 420-bit-reference tape from 151086061 ops to 121342788. Still much longer and costlier than original. 51,058,471 reference-mirror ops and 10,438 rebases.
- Independent KickMix 1.0.0: 256 zero-syndrome cases (zero/random masks), 256 ordinary high weights 18..35, all value/phase/dirty/mask correct. Further boundary panel 64 w35 inputs with S1..S34=0,S35=1, and 64 zero inputs, all clean. Same 32 base boundary inputs at two measurement seeds.
- Exact existing 72-input stratified regression: parent 34 value failures and 19 phase failures (2 with restored values); candidate still 34 value failures, 17 phase failures (0 with restored values); mean paid 316065.02777777775 -> 316424.2638888889 on this diagnostic distribution, not official. Low weights 1..17 remain erroneous. No full repair, accepted cost improvement, official verifier, full Lean proof or score update. Do not promote. The remaining task is repair the arithmetic restoration and HMR witnesses, not more zero-chart corrections.
- Main untouched. No Kaggle submission.

## Reproduce
Use the exact parent hash, KickMix 1.0.0, the existing competition verifier in DQI_VERIFIER_DIR, GNU C++20 and NumPy. The existing 316k parent is not committed as a binary.
```sh
python prepare.py /path/to/old.kmb
g++ -O3 -march=native -std=c++20 shadow_affine.cpp -o shadow_affine
./shadow_affine /path/to/old.kmb qids.txt mask_ids.txt candidate.kmb
sha256sum candidate.kmb
python replay.py candidate.kmb replay.json
```
The physical register map is in verifier order, not ascending qubit order. Reuse the prior proof contracts instead of treating the zero-chart result as a new mathematical framework.
