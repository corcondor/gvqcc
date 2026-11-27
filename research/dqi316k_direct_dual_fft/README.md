# Exact 316K native lineage — research only, NOT SUBMISSION

Parent exact SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52, 900Q, 69782188 ops, 318972 static paid, from Tony Li / tonylica Quantum AI 32.85306 Task Generators v2, Team ThemBones and other upstream contributors. No 410K substitution. First apply exact #239 commuting/dead-gate rewrite to this pinned input. Next use the classical dual-mask check in dual_fft_repair.cpp. If the 4095 trace-dual mask coordinates lie in the evaluation span of X through X^70, the oracle phase is exactly the pairing with the 70 syndrome words; no quantum decoder is needed. Exact Lagrange basis inversion, a recurrence fast-reject and additive-subspace polynomial evaluation certify membership. Complement executes the original decoder unchanged. No host-selected quantum input or inferred error weight, no new paid gates. No claim of universal repair: dense masks retain the inherited low-weight decoder faults. The optimization is mathematically defined for all masks in this subspace; not fitted to any test instances.

Vercel sandbox sbx_yj7MMvoJiGX7VORsw1YX4BlfoFCk, KickMix 1.0.0, same paired inputs and seeds. 2480 shots each. Original 140 union errors in zero and dual mask panels; new 0. Dense panel still 70 errors / 144. Ordinary distribution 0 / 2048 both, mean 316126.84765625 unchanged. Final direct FFT 900Q, 69619210 ops, 318952 static paid, SHA256 b8aa76ba449042184fc2e9952c73cdf1e38abb118bf6799af6e8ba8b2a9ec2f4. Not an official score or full-domain fix. Independent local low-weight guard experiment (not the direct FFT circuit) reduced the #231 transposed interpolation guard, produced 900Q 2967500 static paid, 147651339 ops, 1678 shots: 1633 passed, 45 remaining errors on saved high-weight panel. Rejected for cost and errors. No competition submission.

## Reproduction
Use a hash-verified original native parent; retain upstream notices. From repo root:
```sh
g++ -O3 -std=c++17 research/dqi316k_joint_crt/direct_commuting.cpp -o direct_commuting
./direct_commuting parent.kmb direct316.kmb
cd research/dqi316k_direct_dual_fft
g++ -O3 -std=c++17 dual_fft_repair.cpp -o dual_fft_repair
./dual_fft_repair ../../direct316.kmb directfft316.kmb
python verify_dual.py ../../parent.kmb directfft316.kmb
```
Lean lemma is the abstract bilinear factorization, not full KMB semantics; CI requested, not yet verified.
