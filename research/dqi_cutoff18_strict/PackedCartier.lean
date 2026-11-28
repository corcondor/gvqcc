import Mathlib

namespace GVQCC.PackedCartier
variable {K : Type*} [CommRing K]

/-- The missing kernel coordinate is carried by the complementary quotient. -/
theorem kernel_shear_preserves (a b c d j : K)
    (h2 : ∀ z : K, z + z = 0) :
    a * (c + b*j) + b * (d + a*j) = a*c + b*d := by
  calc
    _ = a*c + b*d + (a*b*j + a*b*j) := by ring
    _ = _ := by rw [h2, add_zero]

theorem bezout_recovers_residue (a b u v c d : K)
    (h : u*a + v*b = 1) :
    u*(a*c+b*d) = c + b*(u*d-v*c) := by
  calc
    _ = (u*a+v*b)*c + b*(u*d-v*c) := by ring
    _ = _ := by rw [h, one_mul]

theorem tag_shear_involution (a b c d j : K)
    (h2 : ∀ z : K, z + z = 0) :
    (c+b*j+b*j, d+a*j+a*j) = (c,d) := by
  rw [add_assoc c, h2, add_zero, add_assoc d, h2, add_zero]

theorem square_add (a b : K) (h2 : ∀ z : K, z + z = 0) :
    (a+b)^2 = a^2+b^2 := by
  calc
    _ = a^2+b^2+(a*b+a*b) := by ring
    _ = _ := by rw [h2,add_zero]

theorem square_sum {I : Type*} (s : Finset I) (f : I → K)
    (h2 : ∀ z : K, z+z=0) :
    (∑ i ∈ s, f i)^2 = ∑ i ∈ s, (f i)^2 := by
  classical
  induction s using Finset.induction_on with
  | empty => simp
  | @insert a s ha ih =>
    rw [Finset.sum_insert ha, Finset.sum_insert ha, square_add _ _ h2, ih]

#print axioms kernel_shear_preserves
#print axioms bezout_recovers_residue
#print axioms tag_shear_involution
#print axioms square_add
#print axioms square_sum
end GVQCC.PackedCartier
