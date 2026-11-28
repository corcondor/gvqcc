import Std.Tactic
import Init.Grind.Ring.Basic

set_option autoImplicit false

namespace Gvqcc.MixedPacking

/-- The reduced evaluation retains the equivalence class of the second
source row modulo the first source row. -/
theorem determinantFromReduced {F : Type} [Lean.Grind.CommRing F]
    (a b u v k h : F) :
    a*(k*b+h*v)-b*(k*a+h*u) = h*(a*v-b*u) := by
  grind

/-- Store the shear coefficient, not the two redundant source values. -/
theorem sourceRestore {F : Type} [Lean.Grind.CommRing F]
    (a u k h j : F) (hj : j*h=1) :
    j*(k*a+h*u)-(j*k)*a = u := by
  grind

/-- Reuse the existing determinant reciprocal to recover the projection
coefficient of the discarded source row consumable by the inverse. -/
theorem projectionShare {F : Type} [Lean.Grind.CommRing F]
    (a b u v k h j : F) (hj : j*(a*v-b*u)=1) :
    j*((k*a+h*u)*v-(k*b+h*v)*u)=k := by
  grind

/-- Normalized reconstruction in characteristic two: the field restoration
formula is coefficientwise ring algebra. -/
theorem restoreFormula {R : Type} [Lean.Grind.CommRing R]
    (l m T S d rho g0 g1 : R) (h : T*T = S*S+d*d) :
    (S*S*l+d*rho*(S*m))*g0+(T*T*m)*g1 =
      S*S*(l*g0+m*g1)+d*d*m*g1+d*rho*(S*m)*g0 := by
  grind

/-- Erasure is phase transparent only after validating the retained-word
identity. With a fault, the same repayment leaves its measurement parity. -/
theorem rowEraseDebt (dot : BitVec 12 → BitVec 12 → Bool)
    (m old x y fault : BitVec 12) (h : old = (x ^^^ y) ^^^ fault)
    (linear : ∀ a b, dot m (a ^^^ b) = Bool.xor (dot m a) (dot m b)) :
    Bool.xor (Bool.xor (dot m old) (dot m x)) (dot m y) = dot m fault := by
  rw [h, linear (x ^^^ y) fault, linear x y]
  cases dot m x <;> cases dot m y <;> cases dot m fault <;> decide

#print axioms determinantFromReduced
#print axioms sourceRestore
#print axioms projectionShare
#print axioms restoreFormula
#print axioms rowEraseDebt

end Gvqcc.MixedPacking
