import Std.Tactic
import Init.Grind.Ring.Basic
set_option autoImplicit false
namespace Gvqcc.ScaleChart

/-- Scaling a root transports the normalized quadratic's linear term.
    The internal chart family is not fixed by this map in general. -/
theorem quadraticTransport {R : Type} [Lean.Grind.CommRing R] (a x k : R) :
    (a*x)*(a*x)+a*(a*x)+(a*a)*k = (a*a)*(x*x+x+k) := by
  grind

/-- The same transport for a squared chart factor. -/
theorem doubleTransport {R : Type} [Lean.Grind.CommRing R] (a x k : R) :
    let z := (a*x)*(a*x)+a*(a*x)+(a*a)*k
    let q := x*x+x+k
    z*z = (a*a)*(a*a)*(q*q) := by
  grind

/-- Pointwise equality of a scaled recurrence term and its common factor.
    The stated products of powers are the exponent bookkeeping hypothesis. -/
theorem termTransport {R : Type} [Lean.Grind.CommRing R]
    (coeff moment fromCoeff fromMoment common : R)
    (h : fromCoeff*fromMoment=common) :
    (fromCoeff*coeff)*(fromMoment*moment)=common*(coeff*moment) := by
  grind

#print axioms quadraticTransport
#print axioms doubleTransport
#print axioms termTransport
end Gvqcc.ScaleChart
