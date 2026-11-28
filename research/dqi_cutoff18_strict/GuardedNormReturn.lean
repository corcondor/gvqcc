import Mathlib
namespace GVQCC.GuardedNormReturn
section Ring
variable {R : Type*} [CommRing R]

theorem cache_frobenius_return (a n i : R) (σ : R →+* R)
    (hσ : σ (σ a) = a) (hi : σ i = i) (h : a = 0 ∨ i * n = 1) :
    σ (σ a * i) * n = a := by
  rw [map_mul, hσ, hi]
  rcases h with ha | hn
  · simp [ha]
  · rw [mul_assoc, hn, mul_one]

theorem distributed_return (b flag u v w : R) :
    b * (u + flag * v + flag * w) = b * u + flag * (b * (v + w)) := by ring

theorem cache_erase_debt (a n i : R) (h : n * i = 1) :
    (a * n) * i = a := by rw [mul_assoc, h, mul_one]

theorem shared_division_step (a b d i : R) (h : d * i = 1) :
    (a * i + b * i) * d = a + b := by
  calc
    _ = (a + b) * (d * i) := by ring
    _ = _ := by rw [h, mul_one]
end Ring

theorem guarded_hmr_return (a b g m : Bool) :
    Bool.xor (m && (g && (Bool.xor a b)))
      (Bool.xor (m && g && a) (m && g && b)) = false := by
  cases a <;> cases b <;> cases g <;> cases m <;> decide

#print axioms cache_frobenius_return
#print axioms distributed_return
#print axioms cache_erase_debt
#print axioms shared_division_step
#print axioms guarded_hmr_return
end GVQCC.GuardedNormReturn
