# Transported hole chart: exact #314 second block (research only)

Parent #314, Lean CI 46148021083 successful. The original second interval has
100 X-free CX/SWAP/CCX gates and 3 CCX. Its entry/exit variable indices are
local labels in the #314 Lean source, not global physical IDs.

**New exhaustive results from independent JavaScript execution:**
- All 128 transported directions w with w_10=1 and zero on each CCX control
  after affine transport. Chosen w=1036, v=5704. Projection y=drop10(s xor
  s_10*v) bijective on all 8192 clean-entry states.
- Measurement s_10=x_0 xor x_3 exactly; can repay using two conditional Z
  operations before nonlinear calculation if a coin was properly produced.
  All 16384 (input,coin) outcomes checked.
- Push all affine maps across the three CCX into one input frame. Three
  generalized shears (full forms l,m,u)=(1,2,1024),(1028,1032,3167),
  (128,256,2139). Deterministic 40000-pivot-order search: last 13x13
  affine map 50 -> 35 gates. Exact encoded core 56 gates, 3 CCX,
  13 local wires; 58 including two phase operations.
- Full canonical arbitrary-dirty 14-wire replacement (no HMR change)
  100 -> 64 gates, 3 CCX, all 16384 inputs exact. Also compatible with
  scope-permutation absorbed form: 74 -> 64 gates, all 16384 inputs exact.
  C++ whole-tape matcher only emits when all opcodes and wire relations
  match, with no conditions inside the block. This is not yet a measured
  whole #314 rewrite.
- Standard projection output has 6144 distinct states (2048 empty,
  4096 singleton, 2048 double fibres). Nonlinear ANF output span rank 3
  for both encodings; three ANDs necessary for unrestricted deterministic
  affine/AND realization. For fixed HMR outcome, canonical local map has
  linear operator rank 6144, unlike 13Q HMR rank at most 4096. Therefore
  independent 13Q canonical realization with exactly that instrument is
  impossible without extra global reachable-state relations or delayed
  erasure. Encoded core retains the ghost label; cannot discard it.
  To return to standard coordinates, h must be recovered from a global
  live relation, or its physical measurement and phase consumers must be
  transported to a valid later seam. Not yet implemented full width.
- #314 canonical SHA256 994ac1f372211f3599912ab7aeba8063e5332190c904769de853c58bdb600fff.
  The current local compute service failed (ClientError), despite recovery
  of archive metadata. Full #314 is not available as a known GitHub Actions
  artifact. CI defaults to exact #279 518d634e... from run 46121065738,
  never silently labels it #314. Can accept pinned #314 through an actual
  available artifact. No full native #314 validation, no new official score,
  no error repair, no merge/submission.
