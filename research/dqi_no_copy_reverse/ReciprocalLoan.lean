import Mathlib
namespace GVQCC.ReciprocalLoan
variable {F : Type*} [Field F]

def norm (sigma : F →+* F) (x : F) : F := x * sigma x

theorem inverse_norm (sigma : F →+* F) (s : F) :
    norm sigma s⁻¹ = (norm sigma s)⁻¹ := by
  by_cases hs : s = 0
  · simp [norm,hs]
  · have hsig : sigma s ≠ 0 := (map_ne_zero sigma).mpr hs
    simp only [norm, map_inv₀]
    field_simp

theorem reciprocal_from_conjugate (sigma : F →+* F) (s : F) (hs : s ≠ 0) :
    sigma s * (norm sigma s)⁻¹ = s⁻¹ := by
  have hsig : sigma s ≠ 0 := (map_ne_zero sigma).mpr hs
  unfold norm
  field_simp

theorem recover_payload (s x t : F) (hs : s ≠ 0) (ht : t = s⁻¹) :
    (x*s)*t=x := by
  rw [ht]
  field_simp

theorem restore_borrowed_coordinate (sigma : F →+* F) (s t : F)
    (hs : s ≠ 0) (ht : t = s⁻¹) (bit : F → Bool) :
    bit (sigma s * (norm sigma s)⁻¹) = bit t := by
  rw [ht, reciprocal_from_conjugate sigma s hs]

theorem erase_norm_using_restored_reciprocal (sigma : F →+* F)
    (s t : F) (ht : t = s⁻¹) : norm sigma t = (norm sigma s)⁻¹ := by
  rw [ht, inverse_norm]

theorem phase_repay (m d p : Bool) :
    Bool.xor (Bool.xor p (m && d)) (m && d) = p := by
  cases m <;> cases d <;> cases p <;> decide

theorem double_phase_repay (m n u v p : Bool) :
    Bool.xor (Bool.xor (Bool.xor (Bool.xor p (m && u)) (n && v))
      (m && u)) (n && v) = p := by
  cases m <;> cases n <;> cases u <;> cases v <;> cases p <;> decide

theorem coordinate_loan_phase (sigma : F →+* F) (s x t : F)
    (hs : s ≠ 0) (ht : t = s⁻¹) (f g : F → Bool) (m n p : Bool) :
    Bool.xor (Bool.xor (Bool.xor (Bool.xor p (m && f t)) (n && g x))
      (m && f (sigma s * (norm sigma s)⁻¹))) (n && g ((x*s)*t)) = p := by
  rw [restore_borrowed_coordinate sigma s t hs ht f, recover_payload s x t hs ht]
  exact double_phase_repay m n (f t) (g x) p

end GVQCC.ReciprocalLoan
#print axioms GVQCC.ReciprocalLoan.inverse_norm
#print axioms GVQCC.ReciprocalLoan.reciprocal_from_conjugate
#print axioms GVQCC.ReciprocalLoan.recover_payload
#print axioms GVQCC.ReciprocalLoan.restore_borrowed_coordinate
#print axioms GVQCC.ReciprocalLoan.erase_norm_using_restored_reciprocal
#print axioms GVQCC.ReciprocalLoan.phase_repay
#print axioms GVQCC.ReciprocalLoan.double_phase_repay
#print axioms GVQCC.ReciprocalLoan.coordinate_loan_phase
