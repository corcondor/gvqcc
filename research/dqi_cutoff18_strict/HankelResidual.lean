import Mathlib

namespace GVQCC.HankelResidual

variable {V R : Type*} [AddCommGroup V] [AddCommGroup R]

/-- Symmetric bilinear pairing in characteristic two: mixed terms cancel. -/
theorem quadratic_add (B : V → V → R)
    (hl : ∀ x y z, B (x + y) z = B x z + B y z)
    (hr : ∀ x y z, B x (y + z) = B x y + B x z)
    (hs : ∀ x y, B x y = B y x)
    (h2 : ∀ a : R, a + a = 0) (p t : V) :
    B (p + t) (p + t) = B p p + B t t := by
  rw [hl, hr, hr, hs t p]
  calc
    (B p p + B p t) + (B p t + B t t) =
        B p p + (B p t + B p t) + B t t := by abel
    _ = B p p + B t t := by rw [h2, add_zero]

/-- Quadratic value is independent of the choice of singular-system solution. -/
theorem solution_independent (B : V → V → R)
    (hs : ∀ x y, B x y = B y x) (z z' : V)
    (h : ∀ x, B z x = B z' x) :
    B z z = B z' z' := by
  calc
    B z z = B z' z := h z
    _ = B z z' := hs z' z
    _ = B z' z' := h z'

/-- If Ht=b+Hp, then p+t is a solution of Hz=b. Here h states
the resulting pairing equality explicitly, not decoder correctness. -/
theorem residual_repay (B : V → V → R)
    (hl : ∀ x y z, B (x + y) z = B x z + B y z)
    (hr : ∀ x y z, B x (y + z) = B x y + B x z)
    (hs : ∀ x y, B x y = B y x)
    (h2 : ∀ a : R, a + a = 0) (p t z : V)
    (h : ∀ x, B (p + t) x = B z x) :
    B z z = B p p + B t t := by
  calc
    B z z = B (p + t) (p + t) :=
      (solution_independent B hs (p + t) z h).symm
    _ = B p p + B t t := quadratic_add B hl hr hs h2 p t

#print axioms quadratic_add
#print axioms solution_independent
#print axioms residual_repay

end GVQCC.HankelResidual
