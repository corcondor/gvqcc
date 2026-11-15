# J6 joint rank-two loader

All thirteen compiled KMBs are 119 qubits and sum to 6,804 CCX per pass.
Independent same-partition compilation would use 8,856; sharing cuts 2,052
from that internal comparison. The actual score11 production family remains
4,030 per pass at J5. At J6 this count gives Q=435, T=20,270 and
a 1.4026467741 chemistry cost ratio at identical reconstructed words and coefficients.
This family does not produce a score improvement.

The partition puts address bits 0–4 in the low bank and bits 5–10
in the high bank. The legal addresses are a Boolean down-set, so the
unconstrained ANF suffix can be completed to the minimum possible rank
for each output matrix. Feature masks use 58 nonlinear bank wires,
and two scratch controls bring the compiled width to 119.

For each selected group of up to five output matrices, choose two vectors
(h_0,h_1) in their common row space. Solve for a two-column matrix (U)
whose columns belong to each matrix's column space and satisfy
(X_i U=I_2), where (X_i A_i=(h_0;h_1)). The rank-two update
(U(h_0;h_1)) lowers every selected rank by exactly two. A single CCX
implements its mixed terms, with CX fanout and pure-low/high correction.
Sharing one update across (k) matrices saves (k-1) CCX over their
separate paired factorizations. Each rank drop and the actual compiled
CCX count were checked. Group selection is heuristic.

Input is the circuit-recovered 1,220×75 uint8 table with raw SHA-256
`8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`.
Its fully padded layout is 13 batches of six words with three final zeros.
The score11 NPZ is supplied for provenance and numerical verification.

Every file was checked over all 1,220 legal addresses with 48 arbitrary
symbolic target bits and all 58 HMR phase coefficients. The check covers
selection preservation, the XOR output delta, clean workspace and
zero measurement-dependent phase. A separate native call to the
unchanged official recovery routine passed both forward and reverse
traversals, using one shot per valid address and seed 2026111506.
The recovered 75 words match exactly. Its total executed 13,608 Toffolis
agree with twice the static sum. This record describes recovery only.

## Reproduce

Use the existing Python environment with NumPy and Kickmix. The repository
dependency is the exact score9 recovered word table and the official verifier
source directory.

```bash
python shared_rank2.py \
  --repo /path/to/gvqcc_repo \
  --source /path/to/score9_rebatch_synth_source_words_1232.npy \
  --factorization /path/to/score11/dfthcsos/submission.npz \
  --verifiers /path/to/verifiers \
  --out rebuilt_family --trials 4
```

Read `family/result.json` for gate/width counts, exact proof details and hashes.
