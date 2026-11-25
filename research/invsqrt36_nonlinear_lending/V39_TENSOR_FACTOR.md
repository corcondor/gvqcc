# V39 — reachable Boolean tensor factors, shared fanout, phase adjoints

Research only / NOT SUBMISSION. Physical whole-circuit peak remains 37Q. No main or Kaggle changes. Exact Boolean factorization over reachable states; this is not a proof or reproduction of the asymptotic tensor geometry results in corcondor/math.

## Independently serialized results

| parent / candidate | native ops | expected paid | all-nonzero cuts |
|---|---:|---:|---:|
| PR100 PR94 donor | 41760 | 25319/16 | 2809 |
| measurement advance | 41828 | 25319/16 | 2719 |
| tensor lifetime | 41922 | 26159/16 | 2620 |
| joint fanout + phase adjoint | 41921 | 26047/16 | 2620 |
| PR97 compact (separate cost parent) | 41950 | 23095/16 | 3149 |
| V39 PR97 budget transfer | 41960 | 23231/16 | 3110 |

PR100 donor SHA 51d20041a28d45a175d9aa2cba372e8086b0841e18d16911730b0a143802920b.
Advance SHA c5745c072d1b6521c23d8df5a860b5a99540ca673c2d08460e40b2687bc6a9b5.
Tensor lifetime SHA 5c8ebcbcd38e181be7c3333f7b7a2406105a37411b709709ff3a50259a6bf7ac.
Joint SHA f819be18a991b4f8fc340ddf5431805940593339eb5138945e9703b0277f13a3.
PR97 parent SHA 114ada6431e2342617685d4e663b225ee211ff1a3e55974114fb3d951f8d63fe.
PR97 transfer SHA 53a9e438fbc066db28f8e472268c8750e44589b316e2dc6dfccb40c764d174c6.

All final candidates use the native KMB bytes; all-domain replay on 3,133,452 legal x and respectively 1276/1278 independent HMR events. Source event matching and group-level comparison of data, phase, rotations, classical records and activation scopes; unchanged gates composed from equal boundaries. Separate mapped physical36 replay of each replacement core. Not standalone fragments or full oracle.

## Search and centralization

37 HMR advancement proposals, 33 exact pass, 22 disjoint selected at zero expected cost overhead, 90 fewer full cuts. New whole-lifetime observable substitution: 295 windows, 2,412,397 sparse cubic probes, 175,905 affine-factor solves, 68 intermediate fits, 17 sampled candidates, 12 exact accepted, 11 selected. Fit a downstream observable L xor A*B or a sparse cubic directly instead of reconstructing the omitted wire. Reversible affine pivot frame, borrowed cubic product, HMR presampling on verified clean survivor. Two groups have their presampling prelude outside the mapped 36Q core. 471 -> 457 body commands under linear compaction. Canonical BDD phase parity bag cancellation then balanced XOR on remaining terms replaced memory-heavy accumulated phase. Whole lifetime result adds 52.5 E.

Centralized common product fanout and guarded compute-phase-uncompute adjoint: four actual groups (core source indices 13764,22487,24507,33925), 8 static paid and 7 E saved versus the tensor stage. The same-guard identity g^2=g allows phase corrections without rebuilding the temporary product. New V39 source algorithms and full exact receipts are packaged in companion ZIP. Low-cost transfer: 8 unique exact source matches, two selected under +8.5 E budget, physical fragments 9 and 130 ops. Independent serialized replay on 1278 events PASS, 39 fewer full cuts. Costs are not additive across distinct parent branches.

## math fork audit and scope

Read README, complete CONTENTS catalogue (730 manuscripts in 375 families), lean/docs/379.md, actual ComparatorChallenges/MatrixExponent.lean, ExactFourier.lean and ArithmeticHierarchy.lean. Most relevant: #379 Euclidean tensor geometry and circuit complexity (shared-bit geometric price suggests separator and reuse costs); #265 PEPS, #281 QAOA, #283 oracle synthesis have incompatible or weaker hypotheses/guarantees for exact KMB. The Fourier statements over fields with invertible group order cannot be imported into GF(2) for 2-power transforms. Asymptotic matrix multiplication bounds do not imply finite Boolean 36Q synthesis. The read comparator files contain statements and sorry placeholders, not universal independent proof verification. Manuscript source paths attempted returned 404. Not an exhaustive source-level audit of all 730 manuscripts.

Reference: https://github.com/corcondor/math/blob/main/lean/docs/379.md ; https://github.com/corcondor/math/blob/main/CONTENTS.md#family-379 . Also literature on tensor-network contraction ordering and modular uncomputation informs local factors and lifetime elimination, not an implementation of a global tensor network package. Lean V39 proves Boolean identities only; exact KMB verification uses independent BDD replay. Full 36Q and official score gain remain unachieved. No main merge.
