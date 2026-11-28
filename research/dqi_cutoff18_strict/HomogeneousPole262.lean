import Mathlib

namespace GVQCC.HomogeneousPole262

variable {R : Type*} [CommRing R]

def forward (g h N D : R) : R × R := (g * D, N + h * D)
def backward (g h U V : R) : R × R := (g * V - h * U, U)

/-- Fraction-free inverse of a continued-fraction step, up to common scale. -/
theorem composition (g h N D : R) :
    backward g h (forward g h N D).1 (forward g h N D).2 =
      (g * N, g * D) := by
  apply Prod.ext
  · simp [backward, forward]
    ring
  · rfl

/-- At a genuine pole a finite quotient cannot be selected:
a Bezout witness would force the nonunit quadratic to divide one. -/
theorem no_finite_head (g N D p r k : R)
    (hd : D = g * k) (hb : p * N + r * D = 1)
    (hn : ∀ t : R, g * t ≠ 1) (h z : R) :
    N + h * D ≠ g * z := by
  intro hz
  apply hn (p * z + (r - p * h) * k)
  calc
    g * (p * z + (r - p * h) * k) =
        p * (g * z) + (r - p * h) * (g * k) := by ring
    _ = p * (N + h * D) + (r - p * h) * D := by rw [← hz, ← hd]
    _ = p * N + r * D := by ring
    _ = 1 := hb

theorem pole_keeps_numerator (g N k : R) :
    forward g 0 N (g*k) = (g^2*k, N) := by
  apply Prod.ext
  · simp [forward]
    ring
  · simp [forward]

/-- Regular chart reconstruction; no division by a vanishing denominator. -/
theorem regular_cancel (g h N D Q : R) (hq : N + h*D = g*Q) :
    N = g*Q - h*D := by
  calc
    N = (N + h*D) - h*D := by ring
    _ = g*Q - h*D := by rw [hq]

theorem pad_residue {F : Type*} [Field F] (g gd n d dd : F)
    (hz : d = 0) (hg : g ≠ 0) (hd : dd ≠ 0) :
    (g*n)/(g*dd+gd*d)=n/dd := by
  rw [hz, mul_zero, add_zero]
  field_simp

end GVQCC.HomogeneousPole262

#print axioms GVQCC.HomogeneousPole262.composition
#print axioms GVQCC.HomogeneousPole262.no_finite_head
#print axioms GVQCC.HomogeneousPole262.pole_keeps_numerator
#print axioms GVQCC.HomogeneousPole262.regular_cancel
#print axioms GVQCC.HomogeneousPole262.pad_residue
