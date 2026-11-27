# Exact 316K #247: grouped Frobenius / additive-subspace multipoint guard

Research only. The frozen #247 donor is reconstructed byte-identically, SHA256 8b9d09f87692f59baaeb399d96650db9389835f23be5c2ab93be4d86259bc6ab. No 410K donor substitution. The original physical decoder is retained in each candidate; these are reduced-cost versions of the diagnostic #253 repairs, not a competitive 316K-cost repair.

## Results (Vercel, KickMix 1.0.0)
- #253 fixed pad: historical 5072065 static paid / 174235218 ops.
- Grouped fixed pad: 4496449 static paid / 163091442 ops, 900Q, 1024/1024 matched forced inputs.
- Multipoint fixed pad: 3673057 static paid / 194268238 ops, 900Q, 1024/1024 matched forced inputs.
- Shared multipoint fixed pad: 3673057 static paid / 173284766 ops, 900Q, 1024/1024 matched forced inputs. On 184 structured probes, 112 value failures (48 low-pad first-pole, 48 high first-pole, 16 high all-pole), no dirty or mask failures.
- #253 adaptive pad: historical 9826681 static paid / 274808787 ops.
- Shared adaptive pad: 7028665 static paid / 272907883 ops, 900Q, 1024/1024 matched forced, 48/48 low-pad first-pole, 72/72 random; high first/all-pole still 64/64 value failures (35 overlapping phase failures). Zero dirty/mask errors.
- All fixed wrapper local tests 144/144. Adaptive pre/post 184/184 each.
- Full shared fixed paid reductions are CCX reductions; CCZ 6716 unchanged. Native receipts record exact hashes and stress means. No official verifier, saved standard failure replay, or Kaggle submission.

## Mathematical changes
1. Group masked Frobenius words across descending target blocks. Exact partition DP lowers the number of masked words from 15964 to 3972 across the 33 reciprocal sizes.
2. Use #251 additive-subspace evaluation points with exact truncated-convolution interpolation. This is a transfer of the mathematics into the guard, not a literal transplant of the #251 410K phase-scan KMB. Independently checked 52577 finite-field tensor coefficients over 74 distinct chunks.
3. Transport source and target linear frames between successive evaluation points; the same 1677362-paid wrapper loses 10491736 operations compared with independent multipoint frames.
4. Use these changes in both coherent adaptive guard maps. The defect in the frozen donor on dense high-pole inputs is not repaired by these changes.
5. Rank42 HMR adjoint experiment is retained as rejected: static paid unchanged, instruction count increased.

Lean 4.35.0 strict local verification of GroupedGuard247.lean (10 theorems) and MultipointGuard247.lean (5 theorems) passed in the same Vercel sandbox. No sorryAx or ofReduceBool. Some theorems use standard Lean axioms. This is not a complete KMB refinement proof.

## Reproduction
Follow FRONTIER_RECEIPT.md to reconstruct frame_joint.kmb. Use the existing #253 invariant247.py / invariant247.cpp, adaptive247.py / adaptive247.cpp and test drivers. Fetch dependencies crt882.py, joint_crt.py, narrow_crt.py, g_guarded.py, joint_phase.py, joint_rank15.py at a52fe81aa92f19b907e3c85813e49998523e1eae. Python 3.13, NumPy 2.2.6, KickMix 1.0.0, C++17.
```sh
python grouped_guard247.py --out invariant247_grouped.kmb
python multipoint_guard247.py --out invariant247_multipoint.kmb
python check_multipoint_tensor.py
python shared_multipoint247.py --out invariant247_shared.kmb
c++ -O3 -std=c++17 invariant247.cpp -o invariant247
./invariant247 frame_joint.kmb repaired_shared.kmb invariant247_shared.kmb pad_words.txt
python test_repaired247.py repaired_shared.kmb
python adaptive_shared247.py --part pre
python adaptive_shared247.py --part post
python -c 'import json; x=json.load(open("adaptive_pads.json")); open("pads2.txt","w").write(" ".join(map(str,x["P0"]+x["P1"]))+"\n")'
c++ -O3 -std=c++17 adaptive247.cpp -o adaptive247
./adaptive247 frame_joint.kmb repaired_adaptive_shared.kmb adaptive_pre.kmb adaptive_post.kmb pads2.txt
python test_adaptive_full.py repaired_adaptive_shared.kmb
python test_repaired247.py repaired_adaptive_shared.kmb
lean -DwarningAsError=true GroupedGuard247.lean
lean -DwarningAsError=true MultipointGuard247.lean
```
The original 316K paid target is NOT met. The next required change is to replace the defective internal decoder stage with a total low-cost projective map, not keep appending wrappers. Do not merge or submit these diagnostic tapes.
