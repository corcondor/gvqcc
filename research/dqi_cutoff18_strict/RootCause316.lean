import Mathlib

namespace GVQCC.RootCause316
variable {F : Type*} [Field F]

/-- Filtering a sequence with a degree-four polynomial changes each
exponential component by that polynomial evaluated at its node. -/
def filter4 (a : F) (s : ℕ → F) (i : ℕ) : F :=
  s (i+4) + s (i+2) + a*s i

theorem filtered_exponential (a c x : F) (i : ℕ) :
    filter4 a (fun j => c*x^j) i =
      c*x^i*(x^4+x^2+a) := by
  simp only [filter4, pow_add]
  ring

theorem filter_add (a : F) (u v : ℕ → F) (i : ℕ) :
    filter4 a (fun j => u j + v j) i =
      filter4 a u i + filter4 a v i := by
  simp only [filter4]
  ring

theorem residual_removed (a : F) (s r : ℕ → F) (i : ℕ)
    (h : filter4 a r i = 0) :
    filter4 a (fun j => s j + r j) i = filter4 a s i := by
  rw [filter_add, h, add_zero]

theorem filtered_magnitude_inverse (e f : F) (hf : f ≠ 0) :
    (e*f)/f=e := mul_div_cancel_right₀ e hf

/-- In characteristic two this is the square of the quadratic node. -/
theorem square_node [CharP F 2] (x k : F) :
    (x^2+x+k)^2 = x^4+x^2+k^2 := by
  have ht : (2 : F) = 0 := CharP.cast_eq_zero F 2
  calc
    (x^2+x+k)^2 =
      x^4+x^2+k^2 + 2*(x^3+x^2*k+x*k) := by ring
    _ = x^4+x^2+k^2 := by rw [ht, zero_mul, add_zero]

theorem zero_mask (bits : List Bool) :
    (bits.map (fun b => b && false)).foldl Bool.xor false = false := by
  induction bits with
  | nil => rfl
  | cons b bs ih => cases b <;> exact ih

end GVQCC.RootCause316
#print axioms GVQCC.RootCause316.filtered_exponential
#print axioms GVQCC.RootCause316.filter_add
#print axioms GVQCC.RootCause316.residual_removed
#print axioms GVQCC.RootCause316.filtered_magnitude_inverse
#print axioms GVQCC.RootCause316.square_node
#print axioms GVQCC.RootCause316.zero_mask
