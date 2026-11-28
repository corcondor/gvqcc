# DQI 316k score-frontier continuation

## Baseline policy
Use the receipt-matched 33.26453-lineage 18-member archive (DQI member SHA-256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52). The name/receipt is not an independently reverified leaderboard score. Preserve the other task circuits. Do not substitute a higher-cost decoder or conflate isolated stage costs with complete-oracle costs.

Comparison parent: #243 combined #239 direct commuting + scoped constant pass, reproduced on Vercel:
1b738200420995367bed19bf6b8a2bba198a9f17f92ce2fae1d3edaaf561258f.
900Q, 66708642 instructions, 318333 static paid.

Candidate successor:
8b9d09f87692f59baaeb399d96650db9389835f23be5c2ab93be4d86259bc6ab.
900Q, 66696654 instructions, 318333 static paid. Net instruction reduction 11988.
Freeze this candidate as the instruction-optimized research successor with the #243 parent retained as the immutable comparison. No score improvement or error repair is claimed.

## Exact transplant
Retain invertible input/output affine frames across the eight existing D16 rank-one product blocks. Check ANF including arbitrary dirty output variables and squares, then restore frames. No ancillas added and all 616 products retained. Raw source build: 69694650 instructions vs 69782188; 87538 saved. After whole-tape commuting and scoped propagation the net improvement is 11988. See frame_raw.json. Both sets of off-diagonal product forms have full column rank (70 and 84), which rules out simple dependencies among these fixed forms, not all possible synthesis. Whole-tape affine and limited ANF searches found zero eligible additional paid reductions; negative search sources preserved.

## Native replay
Vercel session sbx_WgendrobVx9xhu9Ky3cgFj6ii6cn (4 vCPU, 8GB), official pinned runtime from upstream source dataset. Identical samples and measurement seeds for both full tapes. See frontier_score_receipt.json and frontier_forced_receipt.json.
102400 standard shots: both value=1, raw_phase=ancilla=mask=0; all paired bit differences zero; average paid=316130.09541992185 and independent DQI formula cost=306441502849.63837 for both.
1024 forced shots: both union=499, value=488, raw_phase=257, ancilla=mask=0; all paired bit differences zero.
Not an unmodified official verifier run or Kaggle submission. No whole-portfolio score measured.

## Reproduction
Public upstream source dataset tonylica/quantum-ai-32-85306-task-generators v2 extracted at /tmp/source. Run in this directory with C++17 compiler and dependencies numpy/scipy, and set PYTHONPATH=/tmp/source/runtime/kickmix:<dependencies>.
```sh
python /tmp/source/dqi/build.py donor.kmb
c++ -O3 -std=c++17 direct_commuting.cpp -o direct
c++ -O3 -std=c++17 scope_keep_reset.cpp -o scope
./direct donor.kmb direct.kmb
./scope direct.kmb parent.kmb
python d16_shared_frame.py frame_raw.kmb
c++ -O3 -std=c++17 direct_general.cpp -o direct_general
./direct_general frame_raw.kmb frame_direct.kmb
./scope frame_direct.kmb frame_joint.kmb
python score_pair.py parent.kmb 102400 frame_joint.kmb
```
The regenerated instruction order requires direct_general rather than original fixed-offset dead-gate edits. The scoped pass removes the same dead paid gates.

## Remaining work
#245 universal projective chart and #246 D,H phase stage are potential transplant donors, not replacement full decoder baselines. Establish reversible syndrome-to-D,H conversion and existing physical register correspondence first. Reject any full candidate exceeding the current measured score without compensating error improvement. Full 900Q width and inherited forced-input errors remain unresolved. SharedFrame316.lean formalizes the transport and related Boolean identities; exact site equivalence is independently checked by Python ANF, not a full-circuit Lean proof.
