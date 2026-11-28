# #257 paired mask and residual diagnosis

This tests the owner's exact #257 cost baseline, not a larger replacement.
Replayed GitHub artifact 15253960748 from run 46120290199 after checking
archive SHA-256 0150ea29627f9158e63ba2938d4a838edc529eae5a085baf9041b6b7708da8b8
and native SHA-256 81081a88c27b708322f0724a09197814a18646a4a9969984ab9cf76a6e6cd7fa
(900Q, 69,534,364 ops, 318,333 static paid).
The #278 source archive was recovered and its digest separately checked.
Its staged arithmetic code does not implement support recovery in Python;
the main decoder pieces are serialized KMX, so read and compare the real
state at those boundaries before changing gates.

## Same input, four masks

For each of 622 archived and 288 distinct synthetic lanes, fix S and use
the same seed in arms 0, d, m, and m XOR d. Repeat at a second seed. On the
archive m is the exact archived mask, on synthetic lanes m is uniform.
For d use the trace-dual of a random polynomial with exponents 1–70.
The expected phase shift is Tr(sum c_j S_j), independently checked against
the physical magnitudes recovered with Berlekamp–Massey and Forney.
All 622 original archived absolute phases were reconstructed exactly.

Results across both seeds (value/phase counters may overlap):

| Cohort | Zero and pure dual | m value, phase | m XOR d value, phase | Phase covariance failures |
|---|---:|---:|---:|---:|
| Archive, 1,244 paired lanes per arm | 0 | 904, 458 | 904, 462 | 26 (13 distinct) |
| Synthetic, 576 paired lanes per arm | 0 | 272, 131 | 272, 133 | 8 (4 distinct) |

Every paired dense return matches at 840 bits, checked by hashing the
entire XOR residual. All are also seed-stable. None has dirty ancilla or
mask errors. In the synthetic panel all 136 weight 1–17 syndromes fail
value and the other 152 pass value; six dense-arm raw phase errors
in each cohort occur on value-correct replays. All 34 phase-covariance
failures occur on value-failed replays. Identical wrong returns show that
fixing the mask projection alone cannot repair the value defect; equal
phase deltas are not a proof of absolute phase correctness. Zero and pure
dual use the separate exact classical fast path, and cost zero paid here.

## Minimal recurrence of the wrong return

For the 452 distinct archived value errors, compute the GF(4096) minimal
recurrence of S_out XOR S. In **199** cases it factors entirely into the
existing chart quadratics. In 174 of those (weights 3,5,7,9,13,15,17),
all factors have multiplicity two and the observed degree is 38−2w.
The fixed factor sets shrink as w rises; see the receipt. In the remaining
25 of those (five each at weights 29,32,33,34,35), the recurrence is the
single simple Q=X²+X+3169. The other 253 have finite-window complexity
35 (173) or >35 (80); the same chart-factor diagnosis does not explain them.
No wrong return is the zero syndrome. This classification does not assert
the first faulty operation or supply a repair to the circuit.

Three local Lean 4.35.0 lemmas distinguish absolute phase errors from the
covariance residual and prove the cancellation with common HMR debt.
No full-circuit proof, charged-gate reduction, official score, or submission.

## Reproduce

Use KickMix 1.0.0 and the pinned official DQI verifier in PYTHONPATH.
The archive is GVQCC_316K_RANK15_FULL_SPLICE_SOURCE_RECEIPTS.zip
(SHA-256 177db1727be29269489c7870f51e25cf4e415e6131a84da86ee174d8bb0bba4a);
the replay uses only joint_work/audit/saved.bin.
```sh
python paired_mask.py exact257.kmb archive.zip results
python returned_residual.py exact257.kmb archive.zip residuals.json
python summarize.py
lean -DwarningAsError=true PairedMask257.lean
```
