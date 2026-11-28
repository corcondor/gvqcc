# V120 — full DQI optimization and fixed phase counterexample (NOT SUBMISSION)

## Provenance and measured cost
Input V119 KMB SHA256 `ae20114bf0c082dde5dbdae9d144d0404bd2c1f5a71dcf435236ca6d086439c6`.
Its source composition is documented in the previous PR193 comment and V119 reproduction archive.
All counts below are on complete serialized DQI circuits, Q=900. Mean paid is measured on the SAME 4096 official-distribution shots with explicit seed 20261127; not an official two-salt score.

|variant|static paid|mean executed paid|native ops|
|---|---:|---:|---:|
|Fused510|463051|404221.6213378906|63081784|
|V119|459899|400574.2707519531|63214986|
|V120 pass 1|459733|400408.5993652344|63215484|
|V120 pass 2|459683|400356.7731933594|63215634|

V120 SHA256 `6b53245d633cfc744ea79cadcbb3b58ca9527bf9b80a4e0182157904acf62747`.
Both new passes saved 166+50 static paid with no width increase. Actual 4352-shot KickMix replay per candidate (4096 matched distribution plus 256 forced-weight cases), zero value/phase/junk on those panels. **Known fixed witness fails phase on V119 and V120; do not submit.**

Reproduce from hash-pinned V119 using existing `retain_exact.cpp`:
```sh
g++ -O3 -std=c++17 retain_exact.cpp -o retain
./retain V119.kmb pass1.kmb edits1.tsv 160 100000
./retain pass1.kmb V120.kmb edits2.tsv 256 250000
sha256sum V120.kmb
```
The input must match the SHA above. Both retention passes use exact (bounded, conservative) symbolic equality and idle clean wire checks. HMR debt is repaid by the product of the current controls, not stale physical labels. This is not a formal proof of the whole compiler.

## New mathematics
- `LiveSpan.lean`: exact Boolean linear-combination substitution for arbitrary-target CCX and CCZ phase, rebase equality, product HMR phase and stale-control counterexample. Lean 4.35.0 CI [46025060053](https://github.com/corcondor/gvqcc/actions/runs/46025060053) succeeded; only propext where needed; no sorryAx. 
- The complete V119 scan with live affine-dependency-preserving rebases, direct/pair/span searches found **zero** valid reductions (459899 paid gates inspected, 597 span searches, 300 Gaussian searches, zero success). A separate dirty-target echo/cancellation scan also found zero. These are negative experiments for particular abstractions, not a lower bound.
- The additional paid savings use the prior retained-product law, not the unsuccessful live-span pass.

## Fixed failure — do not confuse syndrome consistency with sparse decoding
V118 official default verifier returned status PASS but one phase error; the strict zero-error CI failed. [CI 46023601937](https://github.com/corcondor/gvqcc/actions/runs/46023601937). Independent salt 0/102400. On the exact default distribution seeded by V118 SHA `80281ca28c345d8222b3b18a7fabbf7fffb033c20ddc4050e00e3220ac31ecae`, batch 387 (zero-based), lane 116 fails phase and not value. Replayed entire batch with the same measurement seed and two other seeds. Fused510 (before the V118 changes), V118, V119 pre-retention, V119, V120 ALL fail at lane 116 on each of three seeds; no value errors. The defect is inherited, not established to be caused by the new retention transforms. Fused510's earlier two zero-error salts did not cover it.

Use the pinned upstream verifier from maxoubvd/google-quantum-ai commit a9effc375527bf0b6962c178530d353eb70a3fcb. SeedSequence(base_sha_as_int,pool_size=8).generate_state(3200,dtype=uint64).reshape(-1,2,4), batch387 uses its first four uint64s as input RNG seed and last four as simulator seed, little endian. The witness true weight is 29. E=0 yields zero phase. 64 random triples E1,E2,E1 xor E2 satisfied linearity. All 70 finite field moments probed by transposed multiplication matched the input syndrome. 12 single-bit probes at each of positions 0..69 and 2990 give nonzero words at all 71 positions. A candidate supported exactly there reproduces all 70 syndromes and predicts all 512 independent random phase masks. Positions outside this set were not exhaustively probed for all 12 bits, so report observed weight >=71, not a full proof of physical phase output. The all-position bit-0 scan did find 26 nonzero positions, 25 in 0..69 plus 2990.

`SyndromeCollision.lean` includes actual 29-word and 71-word vectors, using polynomial modulus 0x1053 and primitive element 2. Kernel computation certifies exact 70-moment equality to the recorded syndrome, distinct supports, weights and field-domain bounds. [CI 46025963386](https://github.com/corcondor/gvqcc/actions/runs/46025963386): success, six axiom receipts (none or propext), no sorryAx. This proves the mathematical collision, not complete equivalence of the measured oracle. The correct decoding contract is the unique <=35-weight solution, not merely a solution of 70 syndrome equations. The observed first-70 support suggests the fallback/interpolation contribution survives because locator/scan is wrong, but the first erroneous internal gate or arithmetic stage is not yet identified. Do not mask or special-case the failing input.

## Admission gate
No full strict verifier PASS, competitive score, main merge or Kaggle submission. Keep the research draft. The V120 circuit is a cost-reduction research candidate with a known inherited correctness defect. Next resolve the locator/phase scan contract and only then benchmark two complete salts and combine competitively verified files.
