# DQI unified decoder — correctness-first native candidate

**Research only; not a 316K-cost candidate, not for submission or merge into main.** The original 316K donor is unchanged. This is a complete replacement decoder/phase/uncompute path with the same S0..S69/E0..E4094 ABI, not a partial oracle or precomputed (D,H) input.

## Results
- Native full circuit: 900 qubits = 840 syndrome + 35 degree history + 1 control + 24 shared work.
- 135,840,850 instructions; 14,471,008 static and measured paid operations (CCX); 88,200 HMR.
- SHA256 d50abe8753e7b150658eb7ca3db9db342cfb43e6c88b042799d06be159199e45.
- Native: 406 shots (203 structured fixtures x 2 measurement seeds), plus 635 shots (16 independent random syndromes per weight 0..35 + 35 constant-numerator and 24 all-pole adversaries). All four counters zero in both receipts: restored syndrome, clean workspace, restored classical masks, correct phase. The latter contains 272 low-weight random cases and 16 zero-mask weight-zero cases. Some structured fixtures recur, so 1,041 is execution count, not unique syndromes. No claim of replaying the original exact 272 inputs. No competition score.
- Local word-level reference: 1,078 cases, including 622 saved cases, all zero errors. Not native replay of those saved cases.
- Independent 12-bit inverse template exhaustively compared over all 4,096 field words including zero.

## Build
Requires Python with numpy, scipy, the competition's exact KickMix runtime on PYTHONPATH, and a C++17 compiler (used python -m ziglang c++). Source dependencies reused from the earlier pinned research branches:
```sh
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/a52fe81aa92f19b907e3c85813e49998523e1eae/research/dqi316k_joint_crt/crt882.py -o crt882.py
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/d442f72507472f5d4e1bce77a07f08ab1da2b16f/research/v81/field_scan.py -o field_scan.py
python make_templates.py
python -m ziglang c++ -std=c++17 -O3 unified_native.cpp -o native
./native full full.kmb
sha256sum full.kmb
python verify_full.py
python verify_stress.py
```
The KMB writer includes the empty section 10 and section 11 sentinel and exact classical bit count. The original manually patched KMB was used in the native tests.

## Construction and proof obligations
Replace 630 arithmetic specializations in #248 by 35 common slots, with one-hot endpoint history derived from first nonzero coefficient, controlled rotations and shared reciprocal/packing. On active slots the leading coefficient is nonzero. Pad both numerator and denominator with distinct irreducible quadratics and optionally x; the nonzero roots and their residues are unchanged. The phase scan evaluates D, xD', N and applies a zero-safe inverse before undoing the evaluation. The inverse codec restores all 35 history bits to zero.

For HMR-controlled scaling, computing t=s*a and conditionally swapping it with a leaves the measured word equal to s*a' when f=0 and s^{-1}*a' when f=1 (active branch s nonzero). The respective measured phase character is repaid using the same classical measurement bits; inverse scaling uses the reversed scalar. This is a local algebraic invariant, not a Lean-certified composition theorem.

Next correctness gates: exact saved native regressions, full official verifier and formal composition proof. Do not claim universal correctness or competitive cost on the finite samples. The 14.47M CCX count is a major remaining blocker: the common fixed schedule still evaluates guarded products and field inversions even on inactive branches. No score gain claimed.
