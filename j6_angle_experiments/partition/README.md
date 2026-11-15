# Exact J6 ANGLE loader with two address regions

The best implementation here uses **13 loaders, 127 peak qubits and 6,242 Toffoli per pass**. The unchanged 75 angle words recover in the official forward/reverse loader check on all 1,220 legal addresses. The compiled family is more expensive than score11's 4,030-Toffoli J5 family and is a proof fixture.

The earlier variant with low bits 0–3 in both regions uses 8,042 Toffoli per pass. In the improved variant, the upper 196-row region uses low bits 6 and 7. Three rather than fifteen nonconstant low forms means fewer rank-one terms are needed before paired-rank synthesis. This saves 1,800 executed Toffoli per pass in the compiled loaders, despite the larger upper-region bank.

The common 4/7 complete feature bank takes 80 workspace qubits, but J6 has only 69 available under the 128Q cap. The implementation separates bit 10 with (F(x)=F_0(x mod 1024)+x_{10}(F_1(x mod 1024)+F_0(x mod 1024))). For each stage it forms a cross matrix, pairs rank-one terms, and shares rank-two updates between eligible odd-rank outputs. The auxiliary gates to retain the correct pure-low and pure-high terms are emitted explicitly. Two existing independent feature pivots carry the control parities temporarily instead of requiring dedicated control wires. Workspace used in the first stage is uncomputed by HMR and conditioned CZ and reused in the second. The code is adapted from the repository's score9 paired-rank and nested-care constructions.

The symbolic proof runs on the serialized-and-reloaded KMB and checks all 1,220 addresses, with all 48 arbitrary target bits symbolic. Address and scratch are restored, every formal measurement outcome phase coefficient is zero, and the exact prescribed XOR is performed. This is stronger than a forward-only check on a reachable target. The native forward/reverse check runs the unmodified official loader recovery with one shot per address and counts 12,484 executed loader Toffolis across both passes. Final padding is verified by the official checker. The unchanged official verifier passed all **78,080 shots**. It reports chemistry cost **390,687,530.99986500**, T19146 and Q435, with the same lambda of 46.909655028314184. Substituting this chemistry member alone raises chemistry cost by **32.4868%** and reduces the local aggregate to **24.88176433**. The receipt is in `official_verify.json`.

## Reproduction

Use a Kickmix/NumPy environment and the verifier runtime with SciPy and the official reference data. The exact raw uint8 word table is the repository's `score8_chem_v27_recovered_words.npy`, hash `8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`. Supply score11's coefficient file as `--source`; the compiler copies it byte for byte.

```sh
python build_split_loader.py \
  --words /path/to/score8_chem_v27_recovered_words.npy \
  --source /path/to/score11/dfthcsos/submission.npz \
  --verifiers /path/to/verifiers \
  --correction-low 6 7 \
  --output split_exact_67

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python /path/to/verifiers/dfthcsos/verify.py split_exact_67 \
  > official_verify.json
```

Compare all KMB hashes, gate counts and proof receipts in `split_exact_67/result.json`. Omit the correction split flag to reproduce the first version.
