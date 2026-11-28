# Rank97 via mixed Boolean control planes, research only

Working comparison fixed at 316094.00 mean on the existing matched
1024-shot panel (#314/#319/#320), Q=900. Actual 102400-shot #314 result
316129.03767578123, 0 observed errors, is separate. #320 applies 141
rank99 replacements to #319 and retains mean316094.00 and static317994.

The previous tensor searches kept each operand in its own 24D space.
This experiment allows both controls to be arbitrary forms on their
48D direct sum. Work in exterior 2-forms, preserving the full quadratic
part modulo linear corrections. Compound split-flip visits ranks up to
103, nontrivial 3-to-3 moves on dependent output labels, shared factors,
then exact reductions. New mixed candidates have 99,95,99,96 terms with
mixed controls respectively, out of 99 total. Three runs x four variants:
312000 proposals in the first two, and a further 240000 retaining
equal-rank mixed solutions (552000 total). Best 99, NOT 97. Both
same-side quadratic parts vanish; all 1128 quadratic output words
checked per variant, and 48 linear word corrections emitted. No truncated
99-term list is allowed. Native dirty-target compiler uses two-form
invertible frames and no extra wires; CI tests state and phase forward
and backward. Strict admission rejects all present candidates for <=97.

Additional numerical Hermite/curve place census with the known local
cost table: rational F2 mixed multiplicities best 102; genus1/2 count
screen over F2/F4/F8/F16 minimum99; genus3 count screen did not produce
a <99 cost in these restricted choices. These are search results using
given component bounds, not a theorem about all algebraic curves or
rank. Rambaud WAIFI 2014; Randriambololona J. Complexity 2012.

#319 complete KMB recovered to library materialization path; the local
execution service returns ClientError. Cannot run the new pass on that
physical tape here. #320's independently ANF-checked full splicer
already supports valid shorter normalized tensors, but the mixed-control
extension would require transporting both forms through the two
physical factor maps, including the affine correction. Do not claim a
completed 97-CCX splice, new score, zero-error full decoder, or submission.
