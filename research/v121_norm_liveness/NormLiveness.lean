import Mathlib
namespace GVQCC.V121
variable {F : Type*} [Field F]
def norm (s : F →+* F) (x : F) : F := x * s x
theorem norm_mul (s : F →+* F) (x y : F) :
    norm s (x*y) = norm s x * norm s y := by
  simp only [norm, map_mul]
  ring
theorem norm_inv (s : F →+* F) (x : F) :
    norm s x⁻¹ = (norm s x)⁻¹ := by
  by_cases hx : x = 0
  · simp [norm,hx]
  · have hs : s x ≠ 0 := (map_ne_zero s).mpr hx
    simp only [norm, map_inv₀]
    field_simp
theorem old_word_from_inverse_and_norm (s : F →+* F) (x : F) :
    s (x⁻¹) * norm s x = x := by
  by_cases hx : x = 0
  · simp [norm,hx]
  · have hs : s x ≠ 0 := (map_ne_zero s).mpr hx
    rw [map_inv₀,norm]
    field_simp
theorem erase_cached_norm (s : F →+* F) (x : F) :
    (norm s x⁻¹)⁻¹ = norm s x := by
  rw [norm_inv, inv_inv]
theorem scale_inverse_square_restore (x y : F)
    (hzero : x = 0 → y = 0) :
    (y * (x⁻¹)^2) * x^2 = y := by
  by_cases hx : x = 0
  · simp [hx,hzero hx]
  · field_simp
theorem norm_zero_iff (s : F →+* F) (x : F) :
    norm s x = 0 ↔ x = 0 := by
  constructor
  · intro h
    by_contra hx
    exact (mul_ne_zero hx ((map_ne_zero s).mpr hx)) h
  · intro hx
    simp [norm,hx]
theorem phase_repay (m d p : Bool) :
    Bool.xor (Bool.xor p (m && d)) (m && d) = p := by
  cases m <;> cases d <;> cases p <;> decide
theorem phase_repay_by_reconstruction {A : Type*} (lin : A → Bool)
    (x reconstructed : A) (h : reconstructed = x) (p m : Bool) :
    Bool.xor (Bool.xor p (m && lin x)) (m && lin reconstructed) = p := by
  rw [h]
  exact phase_repay m (lin x) p
end GVQCC.V121
#print axioms GVQCC.V121.norm_mul
#print axioms GVQCC.V121.norm_inv
#print axioms GVQCC.V121.old_word_from_inverse_and_norm
#print axioms GVQCC.V121.erase_cached_norm
#print axioms GVQCC.V121.scale_inverse_square_restore
#print axioms GVQCC.V121.norm_zero_iff
#print axioms GVQCC.V121.phase_repay
#print axioms GVQCC.V121.phase_repay_by_reconstruction
