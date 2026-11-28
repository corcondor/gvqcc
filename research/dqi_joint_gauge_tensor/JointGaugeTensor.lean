import Std
namespace GVQCC.JointGaugeTensor
def xor (a b : Bool) : Bool := Bool.xor a b
theorem quadratic_shared (a b c : Bool) :
    xor (a && b) (a && c) = (a && xor b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem cubic_shared (a b c d : Bool) :
    xor (a && b && c) (a && b && d) = (a && b && xor c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem quadratic_triangle (a b c : Bool) :
    xor (a && b) ((xor a b) && c) = xor ((xor a c) && (xor b c)) c := by
  cases a <;> cases b <;> cases c <;> decide
theorem output_direction (x y p : Bool) :
    xor (xor x p) (xor y p) = xor x y := by
  cases x <;> cases y <;> cases p <;> decide
theorem hmr_linear_debt (a b m : Bool) :
    (m && xor a b) = xor (m && a) (m && b) := by
  cases a <;> cases b <;> cases m <;> decide
theorem guard_cubic_shared (g a b c d : Bool) :
    xor (g && a && b && c) (g && a && b && d) =
      (g && a && b && xor c d) := by
  cases g <;> cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem polar_zero_on_affine (a b c : Bool) :
    xor (xor c (xor a c)) (xor (xor b c) (xor (xor a b) c)) = false := by
  cases a <;> cases b <;> cases c <;> decide
theorem polar_product (a b c d : Bool) :
    xor (xor (a && b) (c && d)) ((xor a c) && (xor b d)) =
      xor (a && d) (b && c) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem coordinate_conjugation {S : Type} (f : S → S) (inv : S → S)
    (h : ∀ x, inv (f x) = x) (P : S → Bool) (x : S) :
    P (inv (f x)) = P x := by rw [h]
theorem seam_congruence {S T : Type} (old new : S → T) (suffix : T → S)
    (h : ∀ x, old x = new x) (x : S) :
    suffix (old x) = suffix (new x) := by rw [h]
end GVQCC.JointGaugeTensor

#print axioms GVQCC.JointGaugeTensor.quadratic_shared
#print axioms GVQCC.JointGaugeTensor.cubic_shared
#print axioms GVQCC.JointGaugeTensor.quadratic_triangle
#print axioms GVQCC.JointGaugeTensor.output_direction
#print axioms GVQCC.JointGaugeTensor.hmr_linear_debt
#print axioms GVQCC.JointGaugeTensor.guard_cubic_shared
#print axioms GVQCC.JointGaugeTensor.polar_zero_on_affine
#print axioms GVQCC.JointGaugeTensor.polar_product
#print axioms GVQCC.JointGaugeTensor.coordinate_conjugation
#print axioms GVQCC.JointGaugeTensor.seam_congruence
