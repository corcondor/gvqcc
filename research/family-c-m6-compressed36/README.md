# Family C m6 compressed MAIN — NOT SUBMISSION

The input is the arithmetic HO reference word U (21 bits), v (6 bits),
and k (4 bits). It is not an integrated inverse-square-root oracle.
The output is a compressed representation of the ring26 word:
22 physical bits, two ordinary residual wires, and four virtual bits
(constant bit25, reconstructed bits24,23,22). The two other wires are free.
The width is measured from actual serialization, not the requested cap.

## Mathematical changes
Use h=floor(U/2^17), z=250+h-12v, w=z+/- (129+2v).
Compute the low 8 bits of z, generate s=[z<0], perform a signed
8-bit add, then transform s to the post-row sign p=[w<0] on the
same physical wire. The pre/post predicates are factored in
Compressed36.lean. The input guard is z+2d>=0, verified on the
reference inputs. The next two quotient digits are recovered by
the exact ESOP tables in the same Lean file. X-measure their physical
wires at the last use, restore the logical values and repay each
measurement phase in the reverse schedule.

## Actual local receipts
- Baseline PR #183 38Q isolated MAIN: 456 expected paid, 4911 physical
  instructions, full physical 26-bit word.
- New compressed 36Q MAIN: initial 696 expected paid; XOR retire
  680; deferred HMR retire 622; factored sign chart **522** expected.
  The final static paid count is 524; 4898 builder ops; 4910 actual
  KickMix instructions; 2198 forward actual instructions.
- All 3,133,452 arithmetic HO reference inputs, two measurement
  histories in builder replay; no top/word/restoration/ancilla/phase errors.
- Independent KickMix 1.0.0 serialization, reloaded binary KMB and
  all 3,133,452 inputs, mean paid **521.9991536490745**, no value,
  restoration, ancilla, or phase errors. KMB SHA-256:
  c16e291867131472167efbf0d1421ccee02d114054f2290a30572d4a0a84c4ed.
- No claim of all measurement histories, physical implementation
  of the virtual-bit END consumer, complete InvSqrt, or score improvement.
  Compared with 38Q/456, the compressed variant is more expensive and
  has a different output interface. Do not submit.
- The bounded Lean statements were written after exploratory simulation;
  certification depends on actual CI. Never equate them to proof of the
  complete physical implementation.

Local executable bundle includes upstream source with licenses, emitted
KMX/KMB, arithmetic and native replay, and receipts.
