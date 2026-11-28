# V86: reachable bilinear synthesis on the actual DQI KMB

Target: pinned public DQI821, SHA-256
`821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3`.
Not the isolated V82 post-locator stage. The original competition syndrome ABI
and all register declarations are retained. No changes to main or Kaggle.

The abstract interpreter starts with arbitrary syndrome bits and zero scratch
as specified by the official verifier. It represents live values as affine
forms in abstract Boolean symbols. New nonlinear products receive fresh
symbols; repeated products are canonicalized using the 2D homogeneous
factor space and Boolean affine corrections. For example,
`a*(a+b) = a*b+a`. A CCX is replaced only if its exact abstract product is
the XOR of at most 32 linear terms from other live wires and a constant. Fixed-factor Gaussian bases also derive products such as a*(b+c) from a*b and a*c; the live-row Gaussian solve is attempted after the one/two-wire fast path. This preserves the
computational-basis action on the reachable subspace, hence also on its
linear span. Conditional writes and branch joins conservatively forget
information. HMR/R reset value tracking; all original phase and measurement
instructions remain in place. Compaction preserves the affine row space but
drops the nonlinear cache. This is not a minimum-rank proof.

The workflow downloads the hash-pinned original KMB, scans every instruction,
writes a new complete KMB only when at least one CCX is removed, checks the
serialized layout and resource counts, then runs the unmodified official
102400-shot verifier. The candidate and receipt are uploaded as CI artifacts.
Initial run [45792856195](https://github.com/corcondor/gvqcc/actions/runs/45792856195): all 364,174 CCX scanned, 2,742 canonical product hits, zero reductions in the one/two-wire pass, 20.80 s. No candidate was written. The extended fixed-factor/live-span pass is separate; no successful reduction or official verifier result is asserted before its workflow completes. No score/seed/salt search or submission.

Reproduce from repository root:
```sh
python research/v86/test_reachable.py
python research/v86/reachable.py source.kmb candidate.kmb --expected-sha 821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3
python verify_dqi_candidate.py candidate.kmb --verifier verify_submission_dqi.py --output official.json
```
