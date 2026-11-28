# Dual-norm screen on the exact 316094.000 complete tape

Research only. No rank-97 full-tape rewrite, Kaggle submission, or score claim.
The pinned #316/#325 900Q baseline is SHA-256
54817e9385f24940585f5a391025152d4a65a36381887ca77b7bab61413ea2ec.
Its complete native mean 316094.000 is on the #325 1,024-input matched panel.

## Verified conditional native kernel

Let K/F be quadratic with F=GF(4096), theta^2=theta+2048 in the field
basis 0x1053, and let bbar be conjugation. With both supplied norms,
let u=N(a+bbar)+N(a)+N(b) and v=N(theta*a+bbar)+2048*N(a)+N(b).
These are Tr(ab) and Tr(theta*ab), respectively, hence
ab=(u+v)+u*theta. Unconditional bilinear rank is not claimed.

Implement using the existing #326/#309/#187 verified 42-CCX
field multiply-add twice. The exact executable local result is 84 CCX,
96Q including existing 24 norm bits, 1,701 ops, not 66 CCX.
The 99 from #311 is 11 x 9, not a certificate for three 33-CCX
GF(4096) multipliers. We would need an actual rank-33 multiplier to
price this construction at 66. With just the norm of b, two mixed
F-linear products cannot represent multiplication (any nonzero output
trace projection has rank-2 cross terms; isolating one product forces
a nonzero pure-a polar term which b-only corrections cannot cancel).

Exact gate ANFs agree on all 96 outputs subject to the stated norm ABI,
with arbitrary dirty target and both inputs restored. Native KickMix
1.0.0: 8,192 forward and 8,192 inverse tests, all pass without phase
errors. KMB SHA-256:
1f670d30d815359902a2d6220d1d1c3d39a9090551de0c6de7830272951e622e.
Do not substitute this kernel without certifying the norm operands and
their physical storage, schedule, cleanup, and phase.

## Actual operand liveness

Replayed the exact #325 donor on the existing 4,096 mixed shots, with
the same reference-generation and HMR seeds. Outputs and counts matched
that run exactly. Reconstructed both norms from the sampled coordinate
maps at all 53 sites where #325 found the full second operand norm pencil.

- B-norm is in the sampled physical affine span at all 53; 10 sites
  already have 12 independent wires directly in the norm space.
- A-norm adds 12 dimensions at all 53: no nonzero A-norm coordinate can
  be recovered as a fixed affine combination of the live input state.
- Also pooled affine spans across 271 earlier/current snapshots and
  every new quantum-wire value in the recorded earlier intervals.
  These intervals cover the previous product to the site if at most
  100,000 ops; for longer gaps, only the preceding product and final
  1,024 ops. 709,788 recorded writes, 2,089,182 ops covered, zero
  A-norm dimensions recovered at all 53. This is an overgenerous budget
  because it permits retaining all witnessed wire functions, free.
- The additional 269 successor snapshots, including the current product
  exit and next product entry/exit, likewise recovered zero A-norm dimensions at all 53 sites.

The negative result rules out fixed affine reuse of exactly those
observed wire functions: any universally valid affine reuse would pass
the sampled rank test. It does not rule out extending the time window,
using dynamic controls, joint producer changes, synthesizing nonlinear
values, or finding a 97-term unrestricted decomposition. Positive
sampled B-norm identities still need a proof of reachability.

## Reproduction

From the #325 source archive, bring `extracted2.tsv`,
`extracted2.tsv.basis`, `norm_relation_receipt.json`, `native.hpp`,
and generate `samples3.bin` with its `generate_samples3.py` and the
pinned official verifier. Do not use or commit the raw captures or
syndrome fixtures. Run with AVX-512 for capture and KickMix 1.0.0/NumPy
for the kernel.

    python landmarks.py
    python eventplan.py
    python futureplan.py
    g++ -O3 -march=native -std=c++17 capture_history.cpp -o capture_history
    g++ -O3 -march=native -std=c++17 capture_events.cpp -o capture_events
    ./capture_history base.kmb samples3.bin history_replay.csv landmarks.txt history.bin
    ./capture_events base.kmb samples3.bin events_replay.csv intervals.txt events.bin events.tsv
    ./capture_history base.kmb samples3.bin future_replay.csv future_landmarks.txt future.bin
    python audit_history.py
    python audit_events.py
    python audit_future.py
    python right_sources.py
    python two_norm_native.py

#326 independent CI receipt: packed return after both residues are
solved, 840Q and 24,276 to 10,500 CCX, 512 matched local samples each
without errors. No cost for generating the half-degree inverses or
integrating raw-S is included. Do not credit those component savings
to the full 316094.000 tape.
