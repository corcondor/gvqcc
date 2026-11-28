import Mathlib

namespace GVQCC.FusedAllGap

/-- Block triangular substitution with shared cross-block transform.
The low and high maps need not be linear for the inverse theorem. -/
def forward {L H : Type*} [AddCommGroup L]
    (low : L → L) (high : H → H) (cross : H → L) (x : L × H) : L × H :=
  (low (x.1 + cross (high x.2)), high x.2)

def backward {L H : Type*} [AddCommGroup L]
    (lowInv : L → L) (highInv : H → H) (cross : H → L) (x : L × H) : L × H :=
  (lowInv x.1 - cross x.2, highInv x.2)

theorem backward_forward {L H : Type*} [AddCommGroup L]
    (low lowInv : L → L) (high highInv : H → H) (cross : H → L)
    (hl : ∀ x, lowInv (low x) = x) (hh : ∀ y, highInv (high y) = y)
    (x : L × H) :
    backward lowInv highInv cross (forward low high cross x) = x := by
  rcases x with ⟨x,y⟩
  simp [backward, forward, hl, hh]

theorem forward_backward {L H : Type*} [AddCommGroup L]
    (low lowInv : L → L) (high highInv : H → H) (cross : H → L)
    (hl : ∀ x, low (lowInv x) = x) (hh : ∀ y, high (highInv y) = y)
    (x : L × H) :
    forward low high cross (backward lowInv highInv cross x) = x := by
  rcases x with ⟨x,y⟩
  simp [backward, forward, hl, hh]

/-- A single branch mask can be shared by all terms of a rank product. -/
theorem shared_control {R : Type*} [CommSemiring R] (f x y z : R) :
    f * (x*y + x*z) = (f*x)*y + (f*x)*z := by ring

/-- Pooling the two HMR debts is exact in characteristic two. -/
theorem shared_hmr (m a b : ZMod 2) :
    m * (a+b) = m*a + m*b := by ring

theorem mask_involution (f a b : Bool) :
    Bool.xor (Bool.xor a (f && b)) (f && b) = a := by
  cases f <;> cases a <;> cases b <;> decide

end GVQCC.FusedAllGap

#print axioms GVQCC.FusedAllGap.backward_forward
#print axioms GVQCC.FusedAllGap.forward_backward
#print axioms GVQCC.FusedAllGap.shared_control
#print axioms GVQCC.FusedAllGap.shared_hmr
#print axioms GVQCC.FusedAllGap.mask_involution
