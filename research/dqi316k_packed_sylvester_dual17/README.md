# Exact 316K donor: joint packed Sylvester + dual17

Research only. Parent donor SHA-256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52. No submission/merge. The full circuit is #261's direct donor nonlinear-region replacement, not the original 316K cost. Do not accept as a competitive candidate.

## Integration
- #245/#246/#254/#259/#261: characteristic-two half-degree Bézout. For D=A²+XB² and N=P²+XQ², gcd(A,B)=1 when D is squarefree. Solve AU+BZ=P, AT+BW=Q. Then B²V=N+D(U²+XT²), V=(Z+XT)²+X(W+U)². At physical roots V=N/D'. Original weighted numerator requires the classical x*U_geom(x) factor to be absorbed into mask.
- New packed inverse modular multiplication: B=qA+r, p=Ah+s, v=r^{-1}s mod A, u=h+quotient(Bv,A). Allocate b-a words for h and a words for v. For each j ascending, add quotient(B X^j,A) times v_j into lower coordinates, then scale its own leading coordinate. The output is u. This works for arbitrary degree gaps, does not require two separate full 33-word RHS registers. Only a word-level reference; dynamic quantum degree control, coefficient transport, workspace and gate costs are not yet solved.
- #237/#241/#244/#261: use outer dual42 and inner GF8 dual-number product with 17 symmetric linear forms, replacing inner separate norm6 and cross12. HMR repays the same tensor. All 4096 input pairs checked by Python. New Lean finite basis statement supplied, not yet checked by Lean.

## Reproduction
Use #261 README's pinned public source, Python 3.13, KickMix 1.0.0, and original donor. From /tmp/seam, copy kernel_joint17.py there, and install #261 joint CRT dependencies from commit bf87158c58b5f183f08798d6d449e42c10177019/research/dqi316k_joint_crt plus general_scan.py from 756605477e736183a041d43e91a3606c2ea2c854/research/dqi316k_joint_crt. Source core_direct.py, splice_direct.cpp, verify_raw.py from #261's directory.
```sh
sed '/^if __name__/i import kernel_joint17\nkernel=kernel_joint17.kernel' core_direct.py > /tmp/native/generators/dqi/src/team/core_dual17.py
python -m ziglang c++ -O3 -std=c++17 splice_direct.cpp -o splice_direct
cd /tmp/native/generators/dqi/src/team
OPENBLAS_NUM_THREADS=1 python -u core_dual17.py /tmp/seam/core_dual17.kmb
cd /tmp/seam
./splice_direct donor.kmb core_dual17.kmb full_dual17.kmb
PYTHONPATH=/tmp/native/google-verifiable-quantum-circuit-compilation/verifiers/dqi python verify_raw.py full_dual17.kmb dual17_receipt.json
PYTHONPATH=/tmp/native/google-verifiable-quantum-circuit-compilation/verifiers/dqi python verify_dual17_distribution.py full_dual17.kmb dual17_distribution.json
```
For the packed test, capture DD, NN from #261 core_direct.py's prefix_check by inserting np.savez('/tmp/seam/key_samples.npz',D=np.array(DD),N=np.array(NN),S=a) after 'DD,NN=read(D),read(N);bad=[]'. Run prefix mode. Run packed_sylvester.py on that NPZ. The existing peer sample had 72 cases, 1260 roots; two RHS traversals, degree-gap counts 1:2088, 5:8, 9:8, 13:8.
