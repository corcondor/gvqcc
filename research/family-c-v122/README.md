# V122 shared recovery — isolated MAIN only, NOT SUBMISSION

Parent PR189 KMB SHA-256 c12d000b33d0e9f760eb7326c61f9539060337851da59a18031a43d0be55cba3.
Apply v122_joint.py in the parent's downloadable reproduction archive directory.
Rebuild with Python 3.13 / KickMix 1.0.0:
```bash
python v122_joint.py
python optimize_joint.py v122_joint
python verify_joint36.py v122_joint_opt
g++ -O3 -std=c++17 verify_joint.cpp -o verify_joint
# run replay_independent.py with candidate name v122_joint_opt
```

## Measured comparison (same compressed output ABI)
| variant | width | exact expected paid (builder) | static paid | serialized KickMix instructions |
|---|---:|---:|---:|---:|
| PR189 joint36_v2_opt |36|438.5|486|5779|
| V122 joint_opt |36|431.5|479|5773|

V122 KMB SHA256 b24828e993d80ba9d7b1c098b133e5b84131a28b59aec92235d32ac01df11cd5.
KickMix full 3,133,452 reference HO inputs: mean paid 431.49886451108875;
zero value, restoration, dirty ancilla and phase errors. Independent C++ bit-sliced KMX replay of all those inputs, each of all-zero, all-one and pseudorandom measurement streams: all four errors zero. These are not exhaustive measurement histories.
The gain is entirely the reverse reconstruction of retired quotient digits 23 and 22 (2 + 5 paid saved). The 16 repeated carry rows are unchanged. No complete InvSqrt, END consumer, new DQI or official score claim.

## Mathematical changes
Row23: g=(a+b+c)(d+p), apply shear c'=c+g, use g=c+c', then undo shear. Three CCX rather than five; arbitrary target XOR and source restoration.
Row22: factor first group as ~b+u*(~b+f+e*~d). Remaining group f*(a*d*~b+b*e) uses a temporary t=a*d, e'=e+t, then t'=t+b*e', conditional selection of t or e. Invert the shear before HMR. Six paid rather than eleven. Local Lean source Recovery.lean is submitted for strict CI; do not claim passing until logs confirm.

## Cross-row carry direction
Bounded row21 chart (v=0..63, floor(U/2^14)=-64..63, nonnegative row26 guard): 8160/8192 care inputs map to 107 (v,next sign) pairs with no collisions. Thus another retired digit is possible in principle. The 14 following length-six carry rows 20..7 can in principle use a third clean wire: upstream R32 inverse cost for L=6 drops 10.3125 to 8.5, a conditional budget of 25.375 paid across those 14 rows. Actual release, inverse schedule and output decoding must fit this budget. The 15-bit post-row chart has no affine, quadratic or cubic interpolation on the tested bounded states (rank calculations); degree-four Gaussian solution has 115 terms. This is not a general lower bound on nonlinear networks. An affine-coordinate ANF search over 21 free truth-table bits did not find a sufficiently cheap realization. No row21 retirement adopted, no cross-row gate saving claimed.
Sample reachability pass over serialized CCX/CCZ found no zero-paid replacement among its tested sparse affine / direct quadratic combinations.
The latest DQI PRs #193–198 report a terminal pole and inherited phase counterexamples; do not treat dual-salt sampled PASS as universal correctness.
