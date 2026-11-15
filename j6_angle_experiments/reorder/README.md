# J=6 ANGLE circuits with a disjoint-edge schedule

The 13 emitted circuits passed the unchanged chemistry verifier at its default
**78,080 shots**. Every circuit uses at most **127** of the 128 allowed qubits.
The complete chemistry job costs **390,320,228.4009933**, up from the accepted
score11's **294,887,882.9465613**. The constructed family is therefore an
experimental result and fails the portfolio improvement criterion.

| Quantity | Accepted J=5 | Fixed-order J=6, same split | Reordered J=6 |
|---|---:|---:|---:|
| ANGLE circuits | 15 | 13 | 13 |
| Maximum ANGLE qubits | 128 | 127 | 127 |
| ANGLE Toffoli per pass | 4,030 | 6,242 | 6,233 |
| Complete chemistry qubits | 427 | 435 | 435 |
| Complete chemistry Toffoli | 14,722 | 19,146 | 19,128 |
| Effective normalization | 46.909655028314184 | same by word recovery | 46.909655028314184 |

The 75 Givens angles and their corresponding tree edges are permuted together.
The permutation has a 777-step adjacent-swap witness. Each swap crosses disjoint
pairs of orbitals, so the rotations commute as operators. The original
parent-before-child order constraint is preserved. All 1,220 reconstructed
vectors agree exactly in the local numerical calculation.

The six-slot schedule search used a reproducible integer proxy over rank
factorizations of successive output XOR deltas. In the proxy, the same natural
low-bit group is used for both address stages. The final compiler uses low bits
6 and 7 in the correction stage, so the measured 9 Toffoli improvement is
reported separately from the proxy's 137-point drop. The search examined
8,000,000 move proposals, 3,122,171 of which were legal. It makes no global
optimality claim.

The emitted KMBs are round-tripped through Kickmix. A symbolic checker proves
the prescribed XOR on all 1,220 legal addresses with arbitrary 48-bit target
inputs and tracks cancellation of each HMR measurement phase, restoration of
the selection and zeroed scratch. The official recovery routine independently
recovers the reordered table in both directions with one shot per address.
The complete official validator then runs all 78,080 shots. The verifier's
submission digest is
`85a6ce3aca9744ec9d619714bf7b3ece926e9405f5769f90c55cd155bd2e052e`.

## Additional gauge experiment

The Givens tree admits intermediate sign choices. At each edge its child
starts at zero. With inherited parent sign `a` and desired parent and child
signs `p,c`, replace the 8-bit stored word `w` by
`((-1)**(p XOR c)*w + 128*(a XOR p)) mod 256`. Choose all terminal signs
identically to preserve the final vector up to sign and thus its projector.
31 edges have two freely assignable output signs; one policy puts the
resulting columns in the first quadrant. On all legal input rows the numerical
signed-vector discrepancy is under `7.8e-16`. That policy and two other gauge
policies were evaluated. The best gauged proxy at the original order was 7,872
versus 7,455 with the original words and tag encoding. These are scoped proxy
results. The official verifier result above uses the original angle words in
the new order.

## Reproduction

Use the current score11 chemistry NPZ (SHA-256
`42be33687903988f5d09e8c2f7fefc093896d841d4648fde32186f499794d347`) and
`score9_rebatch_synth_source_words_1232.npy` (the raw uint8 SHA-256 of its
first 1,220 rows is
`8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`).
The compiler directory contains `build_split_loader.py` from the J=6
split-stage experiment. `VERIFIERS` contains the unmodified `dfthcsos`
package and its reference data. `PYTHON` has numpy and Kickmix.

```sh
"$PYTHON" recode.py --words "$WORDS" --npz "$SCORE11_NPZ" --out proxy
g++ -O3 -std=c++17 schedule.cpp -o schedule
./schedule proxy/fixed_schedule.txt 8000000 20261115 > order.json
"$PYTHON" compile_order.py --order order.json --words "$WORDS" \
    --original-words "$WORDS" --npz "$SCORE11_NPZ" --compiler "$COMPILER" \
    --verifiers "$VERIFIERS" --out rebuilt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH="$VERIFIERS:$KICKMIX_SITE" \
    python "$VERIFIERS/dfthcsos/verify.py" rebuilt > verifier.json
```

The source CLI in the last command uses its default shots, seed derivation,
numerical thresholds and cost model. No Kaggle submission was made.
