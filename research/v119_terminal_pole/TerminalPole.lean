import Mathlib

namespace GVQCC.V119

variable {F : Type*} [Field F]

/-- A zero finite quotient cannot occur with nonzero numerator and denominator. -/
theorem zero_head_requires_pole (n d : F) (hn : n ≠ 0)
    (hh : n / d = 0) : d = 0 := by
  by_contra hd
  exact (div_ne_zero hn hd) hh

/-- With a previously finite denominator, the next numerator is a unit. -/
theorem repeated_node_nonzero_numerator (prev n d : F)
    (hp : prev ≠ 0) (h : n = prev) (hh : n / d = 0) : d = 0 := by
  exact zero_head_requires_pole n d (h.symm ▸ hp) hh

/-- Formal coefficient equations from g/(R+h), at infinity.
No assumption that the quotient is globally finite is made here. -/
theorem infinity_coefficients (a b h0 h1 A B : F)
    (hchar : (2 : F) = 0) (ht : a+h1 ≠ 0)
    (ha : A*(a+h1) = 1)
    (hb : B*(a+h1)+A*(b+h0) = 1) :
    A = (a+h1)⁻¹ ∧ B = A+(b+h0)*A^2 := by
  have hdouble (x : F) : x+x=0 := by
    calc
      x+x = 2*x := by ring
      _ = 0 := by rw [hchar, zero_mul]
  have ha' : A = (a+h1)⁻¹ := by
    have h : A = 1/(a+h1) := (eq_div_iff ht).2 ha
    simpa [one_div] using h
  have hb' : B*(a+h1) = 1+A*(b+h0) := by
    calc
      B*(a+h1) = (B*(a+h1)+A*(b+h0))+A*(b+h0) := by
        rw [add_assoc, hdouble, add_zero]
      _ = 1+A*(b+h0) := by rw [hb]
  constructor
  · exact ha'
  · calc
      B = (1+A*(b+h0))/(a+h1) := (eq_div_iff ht).2 hb'
      _ = A+(b+h0)*A^2 := by
        rw [div_eq_mul_inv, ← ha']
        ring

/-- The last-pole finite-zero-chart tail equations recover both lower coefficients.
u*N(0)=k², v*N(0)²=k²*N'(0). -/
theorem terminal_low_coefficients (k n0 n1 u v : F)
    (hk : k ≠ 0) (hn : n0 ≠ 0)
    (hu : u*n0 = k^2)
    (hv : v*n0^2 = k^2*n1) :
    n0 = k^2/u ∧ n1 = k^2*v/u^2 := by
  have hk2 : k^2 ≠ 0 := pow_ne_zero 2 hk
  have hu0 : u ≠ 0 := by
    intro h
    apply hk2
    simpa [h] using hu.symm
  constructor
  · apply (eq_div_iff hu0).2
    simpa [mul_comm] using hu
  · apply (eq_div_iff (pow_ne_zero 2 hu0)).2
    apply mul_right_cancel₀ (pow_ne_zero 2 hn)
    calc
      (n1*u^2)*n0^2 = n1*(u*n0)^2 := by ring
      _ = n1*(k^2)^2 := by rw [hu]
      _ = k^2*(k^2*n1) := by ring
      _ = k^2*(v*n0^2) := by rw [hv]
      _ = (k^2*v)*n0^2 := by ring

/-- Simple pole at zero: the reciprocal slope, rather than value, carries n1. -/
theorem terminal_simple_pole (k n1 v : F)
    (hk : k ≠ 0) (hv : v*n1 = k^2) : n1 = k^2/v := by
  have hv0 : v ≠ 0 := by
    intro h
    apply (pow_ne_zero 2 hk)
    simpa [h] using hv.symm
  exact (eq_div_iff hv0).2 (by simpa [mul_comm] using hv)

theorem monic_top (a b k x : F) :
    (a*x+b)*(x^2+x+k) =
      a*x^3+(a+b)*x^2+(a*k+b)*x+b*k := by ring

/-- Exact inverse of the valid extraction step (before normalization). -/
theorem finite_step_inverse (n d g h q : F)
    (hq : g*q = n-h*d) : h*d+g*q = n := by
  rw [hq]
  ring

/-- The measurement phase parity is unchanged by a target-only Toffoli
transported across HMR. Valid for arbitrary target q and every result m. -/
theorem hmr_transport (q a b m : Bool) :
    (m && Bool.xor q (a && b)) =
      Bool.xor (m && q) (m && a && b) := by
  cases q <;> cases a <;> cases b <;> cases m <;> decide

theorem guarded_hmr_transport (q a b m guard : Bool) :
    (m && Bool.xor q (guard && a && b)) =
      Bool.xor (m && q) (guard && m && a && b) := by
  cases q <;> cases a <;> cases b <;> cases m <;> cases guard <;> decide

end GVQCC.V119

#print axioms GVQCC.V119.zero_head_requires_pole
#print axioms GVQCC.V119.repeated_node_nonzero_numerator
#print axioms GVQCC.V119.infinity_coefficients
#print axioms GVQCC.V119.terminal_low_coefficients
#print axioms GVQCC.V119.terminal_simple_pole
#print axioms GVQCC.V119.monic_top
#print axioms GVQCC.V119.finite_step_inverse
#print axioms GVQCC.V119.hmr_transport
#print axioms GVQCC.V119.guarded_hmr_transport
