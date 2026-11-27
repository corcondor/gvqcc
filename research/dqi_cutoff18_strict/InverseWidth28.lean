import Mathlib
namespace GVQCC.InverseWidth28
variable {F : Type*} [Field F]
open scoped Classical

noncomputable def scale0 (n a : F) : F := by
  classical
  exact if a = 0 then n else n * a

/-- In-place scalar multiplication can choose either nonzero half as pivot.
The simultaneous zero branch has inverse norm zero, so completion at 0 is safe. -/
theorem select_pivot (a b n : F) (h : a = 0 → b = 0 → n = 0) :
    (if a = 0 then (n*a, scale0 n b) else (scale0 n a,n*b)) =
      (n*a,n*b) := by
  classical
  by_cases ha : a = 0
  · by_cases hb : b = 0
    · simp [ha,hb,h ha hb,scale0]
    · simp [ha,hb,scale0]
  · simp [ha,scale0]

theorem norm_inverse (sigma : F →+* F) (x : F) :
    (x * sigma x)⁻¹ * sigma x = x⁻¹ := by
  by_cases hx : x = 0
  · simp [hx]
  · have hs : sigma x ≠ 0 := (map_ne_zero sigma).mpr hx
    field_simp

theorem zero_norm_inverse (sigma : F →+* F) (x : F) (hx : x = 0) :
    (x * sigma x)⁻¹ = 0 := by simp [hx]

theorem nonzero_phase (x : F) :
    x * x⁻¹ = (if x = 0 then 0 else 1) := by
  classical
  by_cases hx : x = 0
  · simp [hx]
  · simp [hx]

/-- A dirty carrier is restored when the cubic toggle is synthesized with four
quadratic toggles, without allocating any clean scratch. -/
theorem dirty_cubic (a b c d t : Bool) :
    Bool.xor (Bool.xor t ((Bool.xor d (a && b)) && c)) (d && c)
       = Bool.xor t (a && b && c) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases t <;> decide

theorem dirty_carrier_restore (a b d : Bool) :
    Bool.xor (Bool.xor d (a && b)) (a && b) = d := by
  cases a <;> cases b <;> cases d <;> decide

theorem advance_hmr_phase (m x a : Bool) :
    (m && Bool.xor x a) = Bool.xor (m && x) (m && a) := by
  cases m <;> cases x <;> cases a <;> decide

theorem restore_hmr_character (m f p : Bool) :
    Bool.xor (Bool.xor p (m && f)) (m && f) = p := by
  cases m <;> cases f <;> cases p <;> decide

end GVQCC.InverseWidth28
#print axioms GVQCC.InverseWidth28.select_pivot
#print axioms GVQCC.InverseWidth28.norm_inverse
#print axioms GVQCC.InverseWidth28.zero_norm_inverse
#print axioms GVQCC.InverseWidth28.nonzero_phase
#print axioms GVQCC.InverseWidth28.dirty_cubic
#print axioms GVQCC.InverseWidth28.dirty_carrier_restore
#print axioms GVQCC.InverseWidth28.advance_hmr_phase
#print axioms GVQCC.InverseWidth28.restore_hmr_character
