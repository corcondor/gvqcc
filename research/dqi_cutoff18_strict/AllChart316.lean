import Mathlib

namespace GVQCC.AllChart316

/-- Cancellation changes the second-chart norm predicate from cubic to quadratic.
The zero-u case is intentionally included in the separate unsafe predicate. -/
theorem norm_cancel {F : Type*} [Field F] (u c v b : F) (hu : u ≠ 0) :
    (u*c)*v = b*u^2 ↔ c*v = b*u := by
  constructor
  · intro h
    apply mul_left_cancel₀ hu
    calc
      u*(c*v) = (u*c)*v := by ring
      _ = b*u^2 := h
      _ = u*(b*u) := by ring
  · intro h
    calc
      (u*c)*v = u*(c*v) := by ring
      _ = u*(b*u) := by rw [h]
      _ = b*u^2 := by ring

theorem quadratic_line {F : Type*} [Field F] (a b c d p q r s t : F) :
    (a+t*p)*(b+t*q)+(c+t*r)*(d+t*s) =
    (a*b+c*d)+t*(a*q+p*b+c*s+r*d)+t^2*(p*q+r*s) := by ring

/-- Nonzero leading coefficient ensures one of any three distinct scales works. -/
theorem quadratic_three {F : Type*} [Field F] (a b c x y z : F)
    (ha : a ≠ 0) (hxy : x ≠ y) (hxz : x ≠ z) (hyz : y ≠ z) :
    ¬ (a*x^2+b*x+c=0 ∧ a*y^2+b*y+c=0 ∧ a*z^2+b*z+c=0) := by
  rintro ⟨hx,hy,hz⟩
  have h₁ : (x-y)*(a*(x+y)+b)=0 := by linear_combination hx - hy
  have h₂ : (x-z)*(a*(x+z)+b)=0 := by linear_combination hx - hz
  have h₃ := (mul_eq_zero.mp h₁).resolve_left (sub_ne_zero.mpr hxy)
  have h₄ := (mul_eq_zero.mp h₂).resolve_left (sub_ne_zero.mpr hxz)
  have h₅ : a*(y-z)=0 := by linear_combination h₃ - h₄
  exact (mul_ne_zero ha (sub_ne_zero.mpr hyz)) h₅

/-- Correct direction of finite Hermite recurrence, with the known quotient. -/
theorem inverse_step {F : Type*} [Field F] (f g q n : F)
    (hf : f ≠ 0) (h : g*n = f⁻¹+q) : f*(g*n-q)=1 := by
  rw [h,add_sub_cancel_right,mul_inv_cancel₀ hf]

/-- Unit-series exponent factorization used by the in-place reciprocal.
The hypothesis is valid for normalized characteristic-two series modulo X^n,
n ≤ 128; the concrete coefficient implementation is audited independently. -/
theorem reciprocal_power {R : Type*} [CommMonoid R] (u : R) (h : u^128=1) :
    u^(3*5*17 : ℕ)*u=1 := by
  calc
    _ = u^256 := by rw [← pow_succ]
    _ = (u^128)^2 := by rw [← pow_mul]
    _ = 1 := by rw [h,one_pow]

/-- The total denominator degree for low-vs-legal rational alias exclusion. -/
theorem precision_bound (low full : ℕ) (hl : low ≤ 17) (hf : full ≤ 35) :
    low+full ≤ 52 := by omega

theorem branch_undo {A : Type*} (lo hi : A → A) (p : A → Bool)
    (hl : Function.Involutive lo) (hh : Function.Involutive hi)
    (pl : ∀ x, p (lo x)=p x) (ph : ∀ x, p (hi x)=p x) :
    Function.Involutive (fun x => if p x then lo x else hi x) := by
  intro x
  by_cases hp : p x = true
  · simp [hp,pl,hl x]
  · have hn : p x = false := by cases hx : p x <;> simp_all
    simp [hn,ph,hh x]

end GVQCC.AllChart316
#print axioms GVQCC.AllChart316.norm_cancel
#print axioms GVQCC.AllChart316.quadratic_line
#print axioms GVQCC.AllChart316.quadratic_three
#print axioms GVQCC.AllChart316.inverse_step
#print axioms GVQCC.AllChart316.reciprocal_power
#print axioms GVQCC.AllChart316.precision_bound
#print axioms GVQCC.AllChart316.branch_undo
