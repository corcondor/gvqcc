# Research continuation of #313 and #314 (not submission)

- Use actual #313 complete 898Q source; contract numerator phase in the
  live numerator bank, reuse two clean guard4 scratch wires in the later
  product bank, and guard the full leaf by nonzero **public residual mask**.
  This changes expected paid count and physical width, not the underlying
  weighted decoder. Never condition on verifier inputs or inferred error
  locations. The 30-scratch leaf is a design until native build/replay.
- Independent whole serialized-tape affine quotient pass applies to
  hash-pinned #279 and #313 artifacts. It proves Boolean phase identities
  from exact local affine constraints, resets knowledge conservatively
  on nonlinear updates and branch joins, and checks actual emitted counts.
  A reduction on #279 is NOT a reduction on #314.
- #314 actual 100-gate second window: 128 directions transport through all
  affine and nonlinear-control constraints. Initial direction 1036 and
  final 5704 encode the lost q10 bit into output XOR 2632. Exhaustive
  enumeration 8192/8192, local phase coefficient check. This is a
  reversible representation of the full 14-wire state on its 13D entry
  subspace; the ordinary projected state still collides. No full 899Q
  packing or repair claimed.
- #311's 99-product result: partial-output symmetric interpolation on
  GF16 at distinct rational places also has a 99-product floor in this
  restricted family. If d_i denotes the number of retained GF2 output
  functionals at point i, the kernel of the evaluation constraints must
  be contained in f*F16[X]_{<=4}. Any five distinct evaluations of a
  degree<=4 polynomial are injective, so sum d_i - sum(top5 d_i)>=24.
  Exhaustive local symmetric rank per dimension (0,4,6,8,9), enumeration
  of dimension patterns on the 17 points, minimum99. This is NOT an
  unrestricted lower bound for GF(2^24) or joint multi-product synthesis.
- #313 CI 46147277949 measured 898Q, 533579 static, 533188.96875 mean
  (1024 distribution) and 2176 clean total. #314 316112.220703125 mean
  on 2048, inherited stress defects. Neither is a new certified score.
  Pinned #314 binary is not accessible in the current execution environment.
  No partial gate savings added to the full score, no merge/submission.
