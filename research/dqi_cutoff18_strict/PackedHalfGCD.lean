import Mathlib

namespace GVQCC.PackedHalfGCD

section Transport
variable {R : Type*} [CommRing R]

/-- A constant coefficient register carries the current evaluation frame.
    The other registers are unchanged. -/
def transport (old new a : R) : R := a + (new - old)

theorem transport_eval (a old new : R) :
    transport old new (a + old) = a + new := by
  simp only [transport]
  ring

theorem transport_composition (a u v w : R) :
    transport v w (transport u v a) = transport u w a := by
  simp only [transport]
  ring

theorem transport_inverse (a u v : R) :
    transport v u (transport u v a) = a := by
  simp only [transport]
  ring

theorem dirty_accumulation (a p q : R) :
    (a + p) + q = a + (p + q) := by ring

theorem joint_split (a b c d x y : R) :
    (a + x*c)*b + (d + x*y) =
      a*b+d + x*(c*b+y) := by ring

/-- Algebraic low-product certificate: splitting both inputs at a monomial
    introduces no missing low coefficient when the cross and high terms
    are accounted for modulo the truncation monomial. -/
theorem low_product_split (a₀ a₁ b₀ b₁ t : R) :
    (a₀+t*a₁)*(b₀+t*b₁) =
      a₀*b₀+t*(a₀*b₁+a₁*b₀)+t^2*(a₁*b₁) := by ring

theorem packed_modular_product (a b c d t : R) :
    (a+t*c)*(b+t*d) - a*b = t*(a*d+c*b+t*c*d) := by ring

/-- General half-GCD lift: high-part reduction plus the correction from
    discarded low coefficients, before any degree-truncated interpolation. -/
theorem high_low_lift (u v aH bH aL bL t : R) :
    u*(t*aH+aL)+v*(t*bH+bL) =
      t*(u*aH+v*bH)+(u*aL+v*bL) := by ring

/-- Characteristic-independent reversible Euclid step. -/
def euclidStep (q : R) (ab : R × R) : R × R :=
  (ab.2, ab.1-q*ab.2)

def euclidUndo (q : R) (br : R × R) : R × R :=
  (br.2+q*br.1, br.1)

theorem euclid_inverse (q : R) (ab : R × R) :
    euclidUndo q (euclidStep q ab) = ab := by
  rcases ab with ⟨a,b⟩
  simp [euclidStep, euclidUndo]

theorem euclid_congruence (a b q u v : R) :
    u*b+v*(a-q*b) = v*a+(u-q*v)*b := by ring

theorem determinant_step (a b c d q : R) :
    c*(b-q*d)-d*(a-q*c) = -(a*d-b*c) := by ring

theorem packed_reconstruction (a b q r : R) (h : a=b*q+r) :
    r+q*b=a := by rw [h]; ring

theorem packed_remainder_low (aL aH bL bH q r u t : R)
    (h : aL+t*aH = (bL+t*bH)*q+r+t*u) :
    aL-q*bL-r = t*(bH*q+u-aH) := by
  linear_combination h

end Transport

section Interpolation
open Polynomial
open scoped BigOperators
variable {F : Type*} [Field F]

/-- The exact joint interpolation premise is a degree bound on the SUM,
    not on the two products separately. -/
theorem joint_interp {k : Nat} (x : Fin k → F)
    (hx : Function.Injective x) (a b c d : Polynomial F)
    (h : (a*b+c*d).degree < (k : WithBot Nat)) :
    Lagrange.interpolate Finset.univ x (fun t =>
      a.eval (x t)*b.eval (x t)+c.eval (x t)*d.eval (x t)) = a*b+c*d := by
  have hi : Set.InjOn x (↑(Finset.univ : Finset (Fin k)) : Set (Fin k)) :=
    hx.injOn
  have hd : (a*b+c*d).degree <
      ((Finset.univ : Finset (Fin k)).card : WithBot Nat) := by
    simpa only [Finset.card_univ, Fintype.card_fin] using h
  simpa only [eval_add, eval_mul] using
    (Lagrange.eq_interpolate (s := Finset.univ) (v := x)
      (f := a*b+c*d) hi hd).symm

theorem scale_inverse (x p : F) (hp : p ≠ 0) :
    (x / p)*p=x := by exact div_mul_cancel₀ x hp

theorem quotient_step (a p r : F) (hp : p ≠ 0) :
    a/p*p + r = a+r := by rw [div_mul_cancel₀ a hp]

end Interpolation
end GVQCC.PackedHalfGCD

#print axioms GVQCC.PackedHalfGCD.transport_eval
#print axioms GVQCC.PackedHalfGCD.transport_composition
#print axioms GVQCC.PackedHalfGCD.transport_inverse
#print axioms GVQCC.PackedHalfGCD.dirty_accumulation
#print axioms GVQCC.PackedHalfGCD.joint_split
#print axioms GVQCC.PackedHalfGCD.low_product_split
#print axioms GVQCC.PackedHalfGCD.packed_modular_product
#print axioms GVQCC.PackedHalfGCD.high_low_lift
#print axioms GVQCC.PackedHalfGCD.euclid_inverse
#print axioms GVQCC.PackedHalfGCD.euclid_congruence
#print axioms GVQCC.PackedHalfGCD.determinant_step
#print axioms GVQCC.PackedHalfGCD.packed_reconstruction
#print axioms GVQCC.PackedHalfGCD.packed_remainder_low
#print axioms GVQCC.PackedHalfGCD.joint_interp
#print axioms GVQCC.PackedHalfGCD.scale_inverse
#print axioms GVQCC.PackedHalfGCD.quotient_step
