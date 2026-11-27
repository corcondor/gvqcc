import Mathlib

namespace GVQCC.ZeroSafeFieldFrame
variable {F : Type*} [Field F]

noncomputable def completed (c : F) : F := by
  classical
  exact if c = 0 then 1 else c

noncomputable def cleared (c x : F) : F := by
  classical
  exact if c = 0 then 0 else x

theorem completed_ne_zero (c : F) : completed c ≠ 0 := by
  classical
  by_cases hc : c = 0 <;> simp [completed, hc]

theorem completed_after_clear (c x : F) :
    completed c * cleared c x = c * x := by
  classical
  by_cases hc : c = 0 <;> simp [completed, cleared, hc]

theorem split_measurement (z x m : Bool) :
    Bool.xor (m && (z && x)) (m && (!z && x)) = (m && x) := by
  cases z <;> cases x <;> cases m <;> decide

theorem zero_flag_clearing (z x : Bool) :
    (z && x) || (!z && x) = x := by
  cases z <;> cases x <;> decide

theorem transpose_character {I J : Type*} [Fintype I] [Fintype J]
    (A : J → I → ZMod 2) (m : J → ZMod 2) (h : I → ZMod 2) :
    (∑ j, m j * (∑ i, A j i * h i)) =
      ∑ i, (∑ j, m j * A j i) * h i := by
  classical
  calc
    _ = ∑ j, ∑ i, (m j * A j i) * h i := by
      simp_rw [Finset.mul_sum, mul_assoc]
    _ = ∑ i, ∑ j, (m j * A j i) * h i := Finset.sum_comm
    _ = _ := by simp only [Finset.sum_mul]

theorem triple_cycle (a b c d e f : Bool) :
    Bool.xor (Bool.xor (a && c && e) (b && d && f))
      (Bool.xor a b && Bool.xor c d && Bool.xor e f) =
    Bool.xor (Bool.xor (a && d && Bool.xor e f)
      (b && Bool.xor c d && e)) (Bool.xor a b && c && f) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> cases f <;> decide

end GVQCC.ZeroSafeFieldFrame

#print axioms GVQCC.ZeroSafeFieldFrame.completed_ne_zero
#print axioms GVQCC.ZeroSafeFieldFrame.completed_after_clear
#print axioms GVQCC.ZeroSafeFieldFrame.split_measurement
#print axioms GVQCC.ZeroSafeFieldFrame.zero_flag_clearing
#print axioms GVQCC.ZeroSafeFieldFrame.transpose_character
#print axioms GVQCC.ZeroSafeFieldFrame.triple_cycle
