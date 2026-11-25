# V43: temporal tensor frame, common-parent integration

Research only — NOT SUBMISSION. Parent PR103 native SHA256 553f46ba954f4c306f4fbd1080342e2faffe1ef9ba800656e480b3d69ddec54e. Whole physical width still 37. A 37-live cut means all 37 BDD coordinate functions are nonzero, not a certificate of physical width.

| variant | ops | expected paid | 37-live cuts | HMR |
|---|---:|---:|---:|---:|
| PR103 | 41533 | 23143/16 | 2899 | 1280 |
| V42 peer | 41623 | 23223/16 | 2866 | 1280 |
| V43 frame | 41587 | 23143/16 | 2819 | 1280 |
| V43 combined | 41677 | 23223/16 | 2786 | 1280 |

Frame SHA256 1dceb7979691172971b9f87bab5e7b9d34342e24bf84acd995b5f5ae0aecb1e8. Combined SHA256 87342e512bf7bd83b9c0e3683f1ae396ae11c307e0df842fd582c787bc82ee2e. Both independently replayed from serialized KMB on 3,133,452 legal inputs with independent symbolic HMR and aligned classical records, phase ledger, guards, rotations, and final data. Frame 29/29 exact candidate windows, 18 chosen, union with five disjoint V42 edits independently replayed (23/23). No official verifier, no score improvement claim.

## Rechecked V41 persistent tensor results
DQI 99 CCX, 2076 CX, 72 wires; 576 basis pairs, 24 dirty target basis cases, 4096 random cases pass. Chemistry all15 actual banks pass 36570 positive/inverse cases, zero value/scratch/phase errors, 3357 paid and128Q. Not full competition submission. Original V41 Lean was not compiled here.

## Experiments
Joint nonmonotone rank-repair search:351 eligible windows,190520 factor solves,6667860 product columns,879 linear factor solutions,1421 rank transitions,34 record-version rejects,0 completed paths. Common-span multi-erase:265 windows,17614 solves,585742 product columns,0 completed paths. Both restricted searches, not general impossibility results.
Phase frame:790 windows,2370 variants. Maintain x=A z+c and guard-indexed Boolean phase ANF, pull back through X/CX/CCX, flush before HMR/rotation/guard updates and when degree expansion exceeds cap. Example original [9380,9396) fourteen CX into q36, CCX(19,21,36), HMR q21; candidate CCX/HMR first then fourteen CX (same 16 operations and 1 paid, 15->1 37-live cuts). Still contains a 37-live cut.

References: Amy/Lunderville, Linear and Non-linear Relational Analyses for Quantum Program Optimization, DOI 10.1145/3704873, sec4-5; Amy/Ross, Phase-state duality in reversible circuit design, DOI 10.1103/PhysRevA.104.052602. Applied analogous Boolean pullback and debt bookkeeping, not full implementation of those papers. corcondor/math family107 staggered extraction and previous V42 spectral geometry reading are inspiration, not direct finite reversible width theorems.

Companion executable archive GVQCC_V43_TemporalTensor_NOT_SUBMISSION.zip SHA256 c33640cad1cc85c67240fb1d5e09e801d08757d79635e108f3592f81c30ab8d6 contains actual Python scripts, KMBs, receipts and selected V41 reproduction files; original V41 chemistry input archive separately required for fresh chemistry run. This PR stores research record and local Lean identities; not a full circuit Lean proof. No main or Kaggle changes.