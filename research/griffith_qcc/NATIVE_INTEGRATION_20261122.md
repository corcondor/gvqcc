# GVQCC: real 15-bank KMB integration and verification — 2026-11-22

**Outcome: actual native 15-bank ANGLE KMBs were rewritten and verified. Paid Toffoli gain = 0; no new competition score.**

This is a source-to-binary implementation, not another four-bit NN toy. Original public Goodpjw V8 (3,375 paid CCX per pass, 128 qubits) was used unchanged as the input baseline. The V8 family is *older* than public V9 at 3,372 CCX; do not mistake it for the current frontier.

## Real measurements

| Resource | Original native KMBs | Rewritten native KMBs |
| --- | ---: | ---: |
| CX across fifteen banks | 481,724 | **381,676** |
| CX eliminated | — | **100,048 (20.77%)** |
| CCX across fifteen banks | 3,375 | **3,375** |
| Formal GF(2)-proven replaced CX intervals | — | **2,274** |
| Width (each bank) | 128Q | **128Q** |
| Full native legal-address computational replay | — | **36,570 basis states PASS, all 128 wires** |

The source and compiled circuit were compared cut by cut. Every modified interval consists solely of unconditional CX gates; its 128-wire GF(2) linear transformation is identical for **every** possible input. All non-CX instructions and operands are byte-identical, including HMR, CZ_IF, Z_IF, CCX, X and register definitions. Since CX implements a phase-free permutation, formal interval equality implies equality of the full quantum instrument, including arbitrary coherent inputs and every subsequent HMR measurement transcript. A separate 1219-address by forward/reverse by 15-bank full-bitset replay agrees on every physical wire. That replay by itself is a computational-basis check, NOT an HMR phase simulation.

## All 15 real banks

| Bank | Old CX | New CX | Unchanged CCX |
| ---: | ---: | ---: | ---: |
| 0 | 35348 | 30502 | 246 |
| 1 | 35517 | 30235 | 241 |
| 2 | 30877 | 22257 | 218 |
| 3 | 30659 | 23102 | 218 |
| 4 | 31013 | 22161 | 218 |
| 5 | 35528 | 30772 | 241 |
| 6 | 30756 | 22517 | 218 |
| 7 | 35533 | 30575 | 241 |
| 8 | 29666 | 22376 | 213 |
| 9 | 30446 | 22814 | 218 |
| 10 | 30332 | 22569 | 218 |
| 11 | 35772 | 30682 | 241 |
| 12 | 30653 | 24154 | 218 |
| 13 | 29323 | 23221 | 213 |
| 14 | 30301 | 23739 | 213 |

Result 16-file research ZIP SHA256: **65d21de733a4d877e2cd8cbb166b0b13615fd950ebbf0a3f4d91377a95bf377a**. This consists of changed ANGLE KMBs, unchanged submission.npz, and research-only metadata, NOT a full 18-file Kaggle submission. Exact per-file SHA256 and fixed source provenance are included in the separate integration receipt. No original submission or main-branch code was changed.

## Paid nonlinear gate research on the same physical KMBs

Exactly **2,961** pairs of CCX with only unconditional CX between them were screened. **2,528** have second controls independent of the first CCX product; **433** have nonlinear second-controls. Of the 2,528 quadratic cases, **zero** could be merged by identical product polar or identical output direction in this restricted two-gate construction. This is a negative result on simple *two-product* rewrites only. Three-or-more-product simultaneous factorization is not ruled out.

## Implemented into this PR

- native_kmb/real_kmb.py: strict KickMix KMB v2 binary reader/writer, byte-for-byte roundtrip and register preservation
- native_kmb/linear_opt.py: certified CX-only linear synthesis on actual physical wires; rewrites full fifteen-bank KMB family
- native_kmb/native_splice.py: exact physical-wire *pre-first-HMR nonlinear* splice, 1219 x 2 legal basis states, all physical wires, strict decrease in paid CCX required for promotion. Post-HMR nonlinear splicing is rejected pending phase-transcript proof
- native_kmb/full_replay.py: exact actual 15-bank 36,570-state computational replay
- tests/test_native_kmb_integration.py: binary serialization, formal matrix proof, fail-closed nonlinear splice tests

## Commands (from research/griffith_qcc)

    python -m native_kmb.linear_opt --original-angles /absolute/path/to/original/dfthcsos --output /absolute/path/to/new/dfthcsos --attempts 8 --zip
    python -m native_kmb.full_replay --old /absolute/path/to/original/dfthcsos --new /absolute/path/to/new/dfthcsos --npz /absolute/path/to/original/dfthcsos/submission.npz --report /absolute/path/to/full_replay.json
    python -m unittest discover -s tests -v

## Not done

No native verified CCX reduction. No changed real-angle KMB contains fewer paid gates. Official KickMix verifier and two-salt competition scoring were not executed for these circuits; given identical lambda_eff, Q and T, official score *would not* improve from this CNOT-only transformation. The goal is to pass the native 128-wire and HMR cut contract with a genuine multi-product factorization that saves paid CCX, then compare against the newer V9 3,372T reference, before claiming a score gain.

This work closes the original physical-KMB serialization and full 15-bank validation plumbing gap, but NOT the nonlinear synthesis or competition-score gap.


## Post-HMR exact nonlinear splice safety

Added native_kmb/smt_splice.py: any X/CX/CCX-only gate segment, even after a prior HMR, is eligible for replacement only after Z3 proves UNSAT for every possible initial physical-wire assignment that would produce a changed final output. Phase-free gate equality extends this proof to arbitrary superpositions and unchanged HMR phase transcripts. Invalid candidates, SMT UNKNOWN, or unchanged paid CCX are rejected. Tests include a *synthetic* 128Q CCX-CX-CCX to CX-CCX identity (2 paid gates -> 1) and SAT-negative controls. CI passed Python 3.11 and 3.12 with PyTorch and Z3. **No corresponding cheaper native V8 replacement candidate was found.**

## Measured real 3/4 paid-gate window screen

Full formal 128-wire input analysis across all fifteen original V8 KMBs:

| Consecutive CCX separated only by CX | Tested | Quadratic | Nonlinear-output dimension equals original count | Lower-dimensional | Nonquadratic excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 2,765 | 2,445 | 2,444 | 1 | 320 |
| 4 | 2,731 | 2,371 | 2,367 | 4 | 360 |

The five lower-dimensional cases were screened for the availability of a spanning family of polar rank-2 quadratic forms; none passed that restricted 3->2 or 4->3 resynthesis requirement. This does not rule out longer windows, causal nonlinear recomputation, reachable-support factorization, or different HMR schedules. Detailed cut indices are in experiments/real_native_3_4_product_cut_screen_20261122.json.

**Real native Toffoli saving = 0, official scoring not run, full 18-file submission not generated.** This is a working and formally checked integration/safety pipeline, not a score record.
