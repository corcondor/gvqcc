# Direct Hermite replacement on exact 316K lineage

Research only. The original 316K donor is reproduced byte-for-byte (SHA-256 in receipt.json). Keep the original prefix up to the first CCX (index 19,992,090), pull back its linear phase into the classical mask using trace duality, restore the coordinate frame and install a new complete raw-syndrome rational decoder, scan, and inverse decoder. This is a replacement, not an additional repair wrapper. No input-dependent host selection.

The guarded raw prefix from #254 yields weighted N,D. At a nonzero root x, N(x)=e(x) U(x) x D'(x). Split D=A²+XB² and N=P²+XQ². Evaluate the four half-degree polynomials using the #251 additive subspace basis. At the leaf e=((P+sqrt(x)Q)/(sqrt(x)B))²/U(x). #244 joint norm phase is used in a 35-qubit work region with a seven-bit root tree. The classical mask absorbs square and U inverse.

First attempt: unbounded DFS shears touched inactive high words; restoration succeeded but phase failed 40/108. Corrected recursion explicitly carries active degree. Full KMB now passes 996/996 cases including 306 forced pole and 48 all-pole cases, zero value/phase/dirty/mask errors. Cost still exceeds the donor: 543848 static, 543285.5050200804 mean on this stress panel. Neither is an official score.

## Reproduction environment
Use public generator repository maxoubvd/google-quantum-ai at a9effc375527bf0b6962c178530d353eb70a3fcb, Python 3.13, KickMix 1.0.0, and the existing #244/#254 dependencies. Place crt882.py, joint_phase.py, general_scan.py and their imports plus native.hpp in /tmp/seam. Place core_direct.py next to build_team.py in generators/dqi/src/team. The exact 316K donor is generated from its original upstream sources; verify its receipt hash before splicing.

Run core_direct.py prefix for the 72-case weighted rational prefix check, then core_direct.py /tmp/seam/core_fixed.kmb for the actual complete new core. Compile splice_direct.cpp against the existing native.hpp using C++17, and run splice_direct donor.kmb core_fixed.kmb donor_fixed.kmb. Run verify_raw.py donor_fixed.kmb fixed_full.json using the original verify_submission_dqi module in PYTHONPATH. Use the pinned field arithmetic/phase dependencies; changing them can alter the binary hash.

Both Lean files checked with Lean 4.35.0 and -DwarningAsError=true. These are algebraic/conditional composition lemmas, not a formal certificate for every native gate.

Next cost objective: replace the per-root general rational phase kernel (~323505 paid gates across all 4095 points) by a native-compatible half-degree Bezout representation (#246); the prefix+inverse currently account for 220343 paid. The #246 standalone cost is not an additive proven bound until the coordinate conversion and common-factor cases have been implemented and tested. Do not submit this experimental circuit.
