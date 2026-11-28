# Exact #292 integration and selection audit

Research only. Do not mistake a observed clean ordinary panel for a safe complete decoder. No private salt, official score, main merge, or Kaggle submission.

Inputs: #292 ZIP SHA-256 7d9fd29a849a1d10f76df81661f0cf7ad87f0345278397605581836284f87b68 (DQI 2545a84896ba44152eab0db6856a056d23f60869c60fac8e7d1a8788c51e88dd); exact #294 joint-gauge DQI b9f72a7bde001b81e0dc2530618dfa29815038b0bec7a542f75b2e3298d26870; exact #295 static-pool-on-#291 donor ddbd1d660cd7a0d9a8daccfbc3b41bc6e07ea0dc3a205bb9a0422aa148d11828.

**Real native integration.** Ran #293 affine HMR graph on exact #292: 3,635 charts, 50,764 fewer instructions, unchanged static paid, all outputs/paid matched on archived 622 shots. Then composed **#294 → the exact #295 global seven-case phase pool**. Six guard charts passed truth-table/affine checks, 84 → 60 CCZ, total static paid 318287 → 318263, Q=900, +2922 instructions, SHA-256 1a8d9436b5a9af308e1adfbe391776102e77b51029933c80764b667e5b6cc1c5. On both 622 archived and 8192 common ordinary shots the full pool is bit-for-bit equivalent to #294 and pays the same amount. Independent matched 102400-shot AVX-512 gate replay confirms equal cost and error count. This is why the static win is not selected.

**Matched comparison.** For the comparison across the three arms, fix ordinary reference sampling to the same seed source (exact #292, suffix joint99-common-v1), not their different KMB hashes. Independent bit-sliced replay uses different HMR RNG than KickMix but all are paired. Mean paid #292 316131.7295117 → #294 316126.0434766. Error union 1 → 0. Local public reference formula DQI cost 306443086860.63 → 305036650567.66 (−0.45896% on this panel, mostly the one error difference). Direct KickMix on the same 512-input witness batch reproduced the exact #292 position289 with 423 wrong bits, and no value/phase error in either #294 or #294+#295 on that batch. In the separate archived 622, union 457 → 412, value 452 → 407, raw phase 237 → 203, dirty and mask zero. Errors remain; scaling may move bad charts, not prove their elimination. Ordinary 8192 KickMix comparison of #292, #293, #294 and isolated #295 found lowest mean 316121.6477051 on #294, 0 observed errors for each. Rank the tie with #294+#295 by instruction count, so **select exact #294 DQI + all 17 unchanged #292 chemistry/invsqrt members**. Validated ZIP CRC, exact SHA-256 and member integrity. Do not claim a new official score.

**99 CCX structure.** 319 maximal contiguous physical CX/CCX spans each contain exactly 99 CCX. All 319 are quadratic in their entry coordinates, three 33-product pieces in the three sampled charts normalize to GF(4)^2 × GF(16)^3. Full exact certificates (576 basis pairs per block): 315 normalize to multiplication in GF(2^24), four normalize to GF(2^12)[e]/(e²); the latter preserve the tangent/Hermite coefficient, not a generic finite-field block. Diagnostic KickMix counts at real guarded boundaries found 312.3111979 mean calls over 768 ordinary shots and four of four dual-number windows on all ordinary and 272 forced-weight shots. The marker is a CSWAP of two extra zero qubits for diagnostics only; all observed original fields and other paid counts match. Single-output and identical-polar contractions gave no savings. A conservative output-life pass allowing single-sided CZ phase transport found no removable 99-product output. No lower bound for joint tensor, and no claim of 310k. A uniform 20-per-active-call reduction would be about 6246 paid, but has not been built. #281–#287 inverse/Schur kernels are not yet connected at a correct, width- and cost-compatible D,N seam. #296 ghost projector is not a full repair either.

**Formal boundary.** Strict Lean 4.35.0 passed seven local theorems (six axiom-free; one propext and Quot.sound). These cover guard pooling, phase and coordinate transport, and the characteristic-two tangent square, not whole-circuit correctness. #295 arithmetic/cubic implementation price does not imply low-weight restoration.

## Reproduce

Use the pinned #292 archive, #293 Sources/Receipts, and #295 Research Source Receipts. Place the pin of `native.hpp` from #296 head 1ecbf4bc8a1d7e0315880c29c8f941adc23a3cac path `research/dqi316k_joint_crt/native.hpp` next to the C++ audit files. Provide competition verifier and KickMix 1.0.0 on PYTHONPATH.

```sh
unzip -p GVQCC_292_VERIFIED_LOCAL_CANDIDATE.zip dqi.kmb > dqi.kmb
c++ -O3 -std=c++17 dump99.cpp -o dump99
./dump99 dqi.kmb blocks.txt
python tensor_audit.py blocks.txt > tensors.jsonl
python certify_field.py blocks.txt > field.jsonl
python certify_dual.py blocks.txt field.jsonl > dual.jsonl
c++ -O3 -std=c++17 trace_guard.cpp -o trace_guard
./trace_guard dqi.kmb diagnostic.kmb blocks.txt
python guard_replay.py dqi.kmb diagnostic.kmb
python exit_directions.py blocks.txt > directions.txt
c++ -O3 -std=c++17 lifetime_phase.cpp -o lifetime
./lifetime dqi.kmb directions.txt > life_phase.tsv
# Use original #295 source pool_global.cpp and colocated includes.
c++ -O3 -std=c++17 pool_global.cpp -o pool_global
./pool_global joint294.kmb joint294_pool295.kmb
python paired_native.py ordinary8192 joint294.kmb joint294_pool295.kmb
lean -DwarningAsError=true JointFieldPhase.lean
python assemble_candidate.py GVQCC_292_VERIFIED_LOCAL_CANDIDATE.zip joint294.kmb selected.zip
```

Standard-size replay: use make512.py and replay512.cpp from #292 Integration Research (requires AVX512VPOPCNTDQ). Generate 102400 common shots with `make512.py ../dqi.kmb 102400 joint99-common-v1 panel`. Replay all four files for each candidate. `replay132.py` (despite historic name) reads panel1.bin batch 133 and independently replays all 512 cases in KickMix. Source replay receipts are supplied; no raw private fixture is included.
