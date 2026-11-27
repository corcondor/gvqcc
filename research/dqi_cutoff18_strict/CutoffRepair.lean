import Mathlib
namespace GVQCC.CutoffRepair
variable {A B : Type*} [AddCommGroup A] [AddCommGroup B]

/-- If an additive postprocessor fixes two words it fixes their difference.
Two legal weight-18 inputs on identical support can differ in one magnitude. -/
theorem fixed_difference (f : A →+ A) (x y : A)
    (hx : f x = x) (hy : f y = y) : f (x-y) = x-y := by
  rw [map_sub,hx,hy]

theorem fixed_syndrome_difference (S : A →+ B) (L : B →+ B) (x y : A)
    (hx : L (S x) = S x) (hy : L (S y) = S y) :
    L (S (x-y)) = S (x-y) := by
  rw [map_sub,map_sub,hx,hy]

theorem shared_background (S : A →+ B) (L : B →+ B) (x y z : A)
    (hx : L (S (x+z)) = S (x+z))
    (hy : L (S (y+z)) = S (y+z)) :
    L (S (x-y)) = S (x-y) := by
  have h := fixed_syndrome_difference S L (x+z) (y+z) hx hy
  have he : (x+z)-(y+z)=x-y := by abel
  rwa [he] at h

variable {F : Type*} [Field F]

/-- A nonzero error magnitude can be written as a difference of two
nonzero magnitudes by choosing any nonzero b distinct from -e. -/
theorem nonzero_magnitude_pair (e b : F) (hb : b ≠ 0)
    (hbe : b ≠ -e) : ∃ x y : F, x ≠ 0 ∧ y ≠ 0 ∧ x-y=e := by
  refine ⟨b+e,b,?_,hb,?_⟩
  · intro hz
    apply hbe
    calc b = (b+e)-e := by ring
         _ = -e := by rw [hz,zero_sub]
  · ring

theorem inverse_cache_repay (q p a : F) (hq : q ≠ 0) :
    (p*q⁻¹)*a*q = p*a := by
  field_simp [hq]

theorem reuse_square_inverse (q a : F) (hq : q ≠ 0) :
    (a^2*q⁻¹)*q = a^2 := by
  field_simp [hq]

/-- Measurement of a product word and exact phase repayment are identity
on the retained operands, for either measurement result. -/
theorem hmr_product_repay (a b m p : Bool) :
    Bool.xor (Bool.xor p (m && a && b)) (m && a && b) = p := by
  cases a <;> cases b <;> cases m <;> cases p <;> decide

theorem hmr_guarded_product_repay (a b m h p : Bool) :
    Bool.xor (Bool.xor p (m && a && b)) (m && a && b) = p ∧
    Bool.xor (Bool.xor p (h && a && b)) (h && a && b) = p := by
  cases a <;> cases b <;> cases m <;> cases h <;> cases p <;> decide
end GVQCC.CutoffRepair
#print axioms GVQCC.CutoffRepair.fixed_difference
#print axioms GVQCC.CutoffRepair.fixed_syndrome_difference
#print axioms GVQCC.CutoffRepair.shared_background
#print axioms GVQCC.CutoffRepair.nonzero_magnitude_pair
#print axioms GVQCC.CutoffRepair.inverse_cache_repay
#print axioms GVQCC.CutoffRepair.reuse_square_inverse
#print axioms GVQCC.CutoffRepair.hmr_product_repay
#print axioms GVQCC.CutoffRepair.hmr_guarded_product_repay
