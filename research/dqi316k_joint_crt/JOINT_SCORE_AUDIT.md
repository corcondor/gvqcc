# 316K joint score audit — NOT SUBMISSION

Full tape: original 316K donor -> #239 direct_commuting -> #240 fold -> #240 repair.
Vercel rebuilt original source dataset and ran the exact chain, then 102400-shot independent score_direct replay. See joint_score_receipt.json. Fold produced zero additional paid reductions on the #239 parent. Two value failures remain. Cost 307925618805.53265 is worse than #239's independent replay 305042060052.2295; hashes use different sample seeds. No official submission.

Latest #241 four-product chart source and Lean proof are preserved here as a separately validated component (215389 paid, 880Q, 432/432 chart-contract checks, CI 46077791127). This is NOT a full oracle and must not be appended as if its local saving is available globally. #241's full_unified.cpp and its receipt are preserved separately; full tape 900Q/318950 static paid, 456/622 paired forced failures. #238 expensive integrated 901Q tape rejected: 3690518 paid and 120/338 inverse stress failures. The #224–230 width results do not establish an entire 898Q tape. #239 and #240 strict Lean CI passed (46076918788 and 46077088585). New JointBudget316.lean gives local composition obligations, not a global correctness theorem.

Physical integration of #237/#241 shared arithmetic requires a full-domain syndrome-to-canonical chart, exact uncompute/phase debts, compatible register allocation, and removal of the replaced original scan. No all-update physical integration or zero-error claim is made.

Build from independently obtained exact pinned donor (check SHA256 in receipt), using C++17:
```sh
c++ -O3 -std=c++17 research/dqi316k_joint_crt/direct_commuting.cpp -o direct
c++ -O3 -std=c++17 research/dqi316k_joint_hmr/fold.cpp -o fold
c++ -O3 -std=c++17 research/dqi316k_joint_hmr/repair.cpp -o repair
./direct donor.kmb direct.kmb
./fold direct.kmb folded.kmb
./repair folded.kmb joint.kmb
python research/dqi316k_joint_crt/score_direct.py joint.kmb 102400
```
The recorded replay used the pinned source dataset runtime with NumPy 2.2.6 and SciPy. 
