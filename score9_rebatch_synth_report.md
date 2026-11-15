# J=4 joint ANGLE synthesis

The new builder produced all 19 circuits, each using at most 125 qubits. It
reduces the older independent-output construction from 5,434 to **5,197 CCX
per pass**. This is a real reduction of 237 CCX per pass, or 474 in the full
forward/reverse loader contribution. It does **not** beat the accepted score8
family: the resulting chemistry cost is 13.6833% higher. No submission or full
numeric verifier was run for this more expensive candidate.

## Exact inputs and checks

The source is the actual word table recovered from the public v27 circuits,
not the declared table in the NPZ. Its first 1,220 rows have raw uint8 SHA-256
`8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea`.
Twelve extra rows are a fixed native extension recovered from those same
circuits. The NPZ remains the accepted score8 H2-only patch, SHA-256
`da30619d4a668d663adc9f7f0462cfd52ba8684cc5523980f5119dc3ef90302e`.
Its declared table still differs from the actual table in 473 entries; the
circuits and all synthesis calculations use the recovered table.

Every new circuit passed a deterministic proof over all 1,232 addresses,
32 arbitrary symbolic input bits, every HMR branch, preserved selection and
zero workspace. The official `recover_words_from_circuits` then passed the
whole 19-circuit family on all 1,220 required addresses in both directions,
one shot per address, seed 2026111591, with zero word differences. This native
check supplements the exact proof; it is not represented as a full default-shot
numeric verifier run.

## Resource result

| Quantity | Score8 accepted | New J=4 joint candidate |
|---|---:|---:|
| Batch size | 5 | 4 |
| Number of circuits | 15 | 19 |
| Loader CCX per pass | 4,030 | 5,197 |
| Total Toffoli | 14,722 | 17,056 |
| Total task qubits | 427 | 419 |
| Maximum circuit qubits | 128 | 125 |
| Chemistry cost | 294,887,961.3668603 | 335,238,250.0630193 |
| Cost ratio | 1 | 1.1368326075745105 |

The first four circuits use 290 CCX, circuit4 uses285, and circuits5–18 use268.
The fixed feature-bank preparation accounts for80 CCX in each circuit. All
figures include preparation, accumulation and phase-correct cleanup according
to the actual KMB operation statistics. Physical factors and actual words are
identical, so the cost ratio follows from the official resource product.

## New exact output-basis search

For the fixed split into four low and seven high address bits, every non-tag
output has a 15×76 cross-partition coefficient matrix. The C++ search enumerates
all32,767 nonzero left-null vectors. For each, it computes the entire kernel in
the 28-dimensional output-coefficient space. Their union contains every output
XOR whose matrix has rank below15. A greedy minimum-weight linear basis then
minimizes the sum of `ceil(rank/2)` over independent output coordinates.

For batches0–3, the union contains only the zero output. Every nonzero output
XOR has rank15. For batch4, it contains zero and one nonzero low-rank output.
For batches5–18, it contains zero and the15 nonzero combinations of the four
LSB outputs. Thus an arbitrary output CNOT basis by itself does not improve
the old per-output paired-rank result.

This is a complete result only for **the fixed4/7 split, fixed native
1,232-address extension, and independent paired-rank output blocks after an
arbitrary output basis**. It is not a circuit lower bound. In particular, the
12 unrequired rows can be completed differently, and products shared by several
outputs fall outside that class.

## New shared-product construction

For two rank15 slices A and B in the same low basis, choose two different low
basis functions l1,l2 and let A1 and B2 be the corresponding high coefficient
functions. Define

    S = l1*A1 XOR l2*B2.

Both A XOR S and B XOR S have rank at most14. For every pair in the actual
candidate their ranks were checked to equal14. The shared S has rank at most2
and is implemented by a single mixed product with CNOT fanout into both outputs:

    (l1 XOR B2)*(l2 XOR A1)
      XOR l1*l2 XOR A1*B2 = S.

The last two terms are pure-low and pure-high functions, so the prepared
complete feature banks implement their corrections with CNOTs. The two
residual slices cost seven products each. The pair therefore costs15 CCX
instead of16. Pairing all rank15 slices saves14 CCX in each of batches0–3,
13 in batch4, and12 in each later batch:237 in total.

The builder verifies the full truth-table residual after all products, including
arbitrary output direction masks. It only emits a circuit if that residual is
exactly additive in the low and high partitions; no discarded quadratic terms
or approximate equality are accepted.

## Reproducible implementation and artifacts

- `score9_rebatch_synth_rank_basis.cpp`: complete left-null enumeration.
- `score9_rebatch_synth.py`: basis optimization, joint products, circuit builder,
  exact proof and official native family recovery.
- `score9_rebatch_synth_source_words_1232.npy`: complete fixed native extension,
  92,528 bytes, file SHA-256
  `792e1b06ca6e4e7b5fa82c3cc96412b9e2d2d70a27edcd7ccb08eb242714bf68`.
- Working candidate: `/workspace/scratch/3815fb5fae06/score9_rebatch_synth/joint`.
- `joint/result.json`: full resource and validation receipt.
- `joint/k00_result.json` through `k18_result.json`: per-circuit ranks, basis,
  proof results and KMB hashes.
- `joint/polytof/data/cpd/comm/92xx-*.npy`: joint product seeds for subsequent
  cross-only tensor optimization. Factors use91 coordinates:15 low monomials
  followed by76 high monomials; output masks use the transformed28-bit basis.

An initial formal COMM search from two independent-output seeds was interrupted
after no saved reduction, because it freezes unnecessary pure-low/pure-high
quadratic terms. No global no-improvement claim is based on that interrupted
search.

The subsequent cross-only quotient search is complete for representative
batches0 and5:50 seconds each,76,140,195 proposed moves and36,836,211 accepted
moves in total. It retained210 and188 mixed products respectively, with exact
cross-tensor equality checked in C++. These bounded searches found no further
reduction; they do not establish global optimality.

`score9_rebatch_matrix_build.py` independently compared the exported batch5
cross tensor against the original joint seed, grouped its376 rank-one terms by
output direction, paired them into188 mixed products, and rebuilt a268-CCX,
125-qubit circuit. Its arbitrary-target, all-HMR-phase proof passed on all1,232
addresses. The existing19-circuit family was left unchanged. The adapter receipt
is `score9_rebatch_matrix_report.json`; raw search inputs and results are retained
as `score9_rebatch_matrix_k0_*` and `score9_rebatch_matrix_k5_*`.

Attribution is retained for the public maoxin123 chemistry loader family and
the repository's earlier `outcome_chem_j4_synthesize.py` helpers. Optional COMM
search uses the unmodified Polytof implementation from ZIB-IOL/polytof (MIT).
The rank enumerator and the shared-pair synthesis logic above are new in this
work. No prior score8 or outcome files were modified.
