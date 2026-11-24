# V13: moving nonlinear gauge with transcript-aware measurement deferral

Research only. Parent PR59 width SHA256 ea605794431d64a22de189087a6c637bf73650b19068dff106755a1798576eca. No main change or official submission.

## Actual results
| stage | source coverage /60766 | instructions | static paid | expected paid |
|---|---:|---:|---:|---:|
| PR59 wide |55829|41868|1871|1692.9375|
| Four initial bridges |55985|41882|1877|1697.9375|
| Six bridges incl. real deferred HMR |56059|41883|1880|1700.4375|
| Moving gauge |56059|41874|1877|1698.9375|
| Final normalized-record phase pruning |56059|41851|1877|1698.9375|

Final actual native SHA256 bb6b451b7d04bceca830211652fee9359bdcceb647a21584f91ef19520631059. Fresh replay of serialized final against exact PR59 parent: 41,704 comparisons; all 3,133,452 legal inputs; 1,186 independent parent HMR variables; five erased outcome events; one deferred event preserves identity; exact transcript phase coefficient ledger zero; final classical memory, data, guards and rotation controls equal. New chart source spans [21386,21431), [25112,25155), [26189,26233), [27227,27267), [27754,27783), [28272,28301), total 230 instructions. All physical indices in chart bodies <=35. Overall circuit still 37Q, 537 operations touching q36 before zero-phase pruning, 4,707 original instructions outside charts. No official verification or score improvement.

## Structural construction
Instead of reconstructing a parked arbitrary value using an affine-plus-product decoder, use the reversible encoding S_v(x)=x xor v f(x), f=a xor ab, with v_c=1, v_a=v_b=0. Then p=c xor f is carried in physical c while the parked independent value is preserved. CX/SWAP transport the direction v, not only the individual scratch value. For quadratic phase terms, substituting x+vf gives a correction f times the Boolean directional derivative; choose v to cancel or simplify that correction. Five nonlinear-borrow spans searched with 332 starting directions total, 8,275 unit evaluations, up to 258 live DP states; three improved by one static CCZ each, 1.5 expected paid saved relative to six-bridge construction. Candidate families: initial direction c plus up to two extra active coordinates, direct gauge change from up to 12 cheapest active paths, exact affine direction transport, guard-grouped polynomial synthesis. Not unrestricted optimality.
Initial screen: 91 residual wide gaps; five constructed reversible replacements; four admitted in combined full replay. Consumer echo case initially rejected because a later conditional overwrite could leave the original classical record live. Fix: remove paired HMR/CZ phase, generate the same independent outcome later by a real HMR on the already-reset q22, reordering event IDs explicitly. The migrating carrier case cancels p xor ab=a xor c, then swaps the parked original value into the exit slot. Final pass deletes exactly 23 phase instructions whose normalized record is dead until overwrite, rechecks actual bytes. Do not repeat same bounded gauge family with only seeds.
Five local equivalences normalize the eliminated measurement result to zero. That alone is not a physical measurement proof: the exact full-trace phase ledger and final classical-state equality discharge the removal. Deferred HMR case preserves arbitrary outcomes, compares their records, and never postselects. Lean certificate source: MovingNonlinearGaugeV13.lean, six actual gate-list and width/count lemmas, three generic Boolean identities. CI must be checked separately. Not a full Lean quantum-channel theorem.

## Conditional scoring
Model inherited from PR43: S(Q,E)=33.17031640530013*(60927.54794503887/(Q*(E+240.37798500105055)))^(1/3). V13 wide: 31.41020598 at 37Q, hypothetical 31.69838911 at 36Q; >246.88359764 expected paid reduction needed at full36 to beat reference. PR59 cost remains 1,673.4375 expected, hypothetical full36 31.83855331. No arithmetic addition of different candidate gains.

## Additional reading
- Khattar & Gidney, Rise of conditionally clean ancillae for efficient quantum circuit constructions, Quantum 9 1752 (2025), https://doi.org/10.22331/q-2025-05-21-1752 ; motivates exploiting existing unknown-state wires, distinct from V13's exact reversible gauge.
- Liu, Zhou & Meng, Quantum Uncomputation of Clean and Dirty Ancilla Qubits (2026), https://arxiv.org/abs/2608.09578 ; structured store-use and dirty uncomputation.
- Yang & Yuan, MBUndo (2026), https://arxiv.org/abs/2611.02345 ; previous reference retained, relates static measurement admissibility to correction synthesis.
- DeCross et al., Qubit-Reuse Compilation, https://doi.org/10.1103/PhysRevX.13.041057 ; previous reference retained. No claim of world-first mathematics or implementing these external solvers.
Reproduction archive contains pinned PR59 parent, exact BDD module, compiler scripts, receipts, logs and native result. Run v13_borrowed_coordinate.py, v13_extend.py, v13_gauge.py, v13_prune.py in archive root. No complete36Q or official verifier; historical ANGLE audit remains incomplete.
