# Total 900Q native DQI rebuild — correctness baseline, NOT SUBMISSION

This is a complete new physical decoder, not a local patch or substitution of the frozen 316k donor. The native input is exactly the original 70 syndrome words and 4095 classical mask words. No Python decisions based on input, no externally chosen chart, no HMR. All 35 boundary bits are coherent and erased.

## Actual Vercel KickMix 1.0.0 result

- Session sbx_Wx66Jjv8e6QJfVBiq7hsdWW5y0DL.
- Build cmd_b4ffa776bbff4fdda5ba3dde09ef; finalization and verification cmd_42021b7640f5434abc0d8eda634c.
- 900Q, 92,253,336 native instructions, 13,207,902 static and measured mean paid.
- Final KMB SHA256 a025a17e88e114e7d2971ca3e5f7853d5a6c06faf89f7c2bb3a7651458786be1.
- Independent fresh 456 syndromes, two seeds, 912/912 PASS; zero value/mask/dirty/phase errors.
- Stratified: w0 16, w1..17 272, w18..35 288. Constant numerator 140, forced quadratic 132, all-pole 64. All 912 passed.
- Prior exact 622 saved syndromes were not replayed on this KMB in Vercel. No unchanged official verifier, private-salt verification, score or Kaggle submission.
- 13.2M paid is much too expensive relative to 316K. This is an error-free-on-tested-panel correctness baseline, not a competitive candidate or universal proof.

## Algorithm

35 fixed slots. Coherent unary prefix mark creates one-hot next boundary. Variable leading-zero run is moved by controlled word rotations. Normalized truncated series reciprocal uses odd powers 3, 5, 17 in characteristic two and fixed triangular loops. Continued fraction quotient packing uses common reversed layouts and variable-length coherent rotations rather than 630 separate reciprocal kernels. Terminal root-free squarefree padding is added to the zero suffix before continuant reconstruction. The 35+35 polynomial words hold monic D (implicit leading coefficient) and N. Scan directly evaluates D(x), x D'(x), N(x) on every nonzero GF4096 point. For D(x)=0 phase is computed from N(x)/(xD'(x)); inverse of zero is explicitly zero in the physical field primitive. Scan and all prefix steps are undone. Dirty borrow in multi-control X and controlled rank-42 multiplication is restored. No arithmetic is delegated to the host during native verification.

Register budget: 840 syndrome/data wires + 35 coherent boundary bits + 1 flag + 24 shared field work = 900. The field inverse uses two nested quadratic towers and a three-bit inverse permutation; all temporary words are restored. #248's reference and #237's 42-CCX rank circuit are reused. The earlier #246 half-degree phase stage is not used in this correctness-first version.

## Reproduce

Python 3.13, KickMix 1.0.0, NumPy, C++17 (Vercel: ziglang).

```sh
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/d442f72507472f5d4e1bce77a07f08ab1da2b16f/research/v81/emit_opt.cpp -o emit_opt.cpp
curl -fsSL https://raw.githubusercontent.com/corcondor/gvqcc/a52fe81aa92f19b907e3c85813e49998523e1eae/research/dqi316k_joint_crt/crt882.py -o crt882.py
python build.py
c++ -O3 -std=c++17 total.cpp -o total
./total full total.kmb
python finalize.py total.kmb
sha256sum total.kmb
python verify.py total.kmb 64
```

The generator is deterministic, the KMB is regenerated rather than committed as an 829 MiB binary. The independent verifier reads the public register ABI directly. Optional fourth argument to verify.py is a saved NPZ fixture with S,M,expected arrays.

Next competitive work must replace the expensive fixed-slot reciprocal/controlled scaling schedule and integrate a narrow shared phase kernel, not mutate the proven-invalid donor. Do not accept a cost improvement unless raw-input whole-circuit regression remains clean.
