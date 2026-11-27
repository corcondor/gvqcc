import InvariantPad
namespace GVQCC.AllPoleChart
open scoped BigOperators
open Polynomial
variable {F : Type*} [Field F]

/-- For legal nonzero support at most 35, a root-free filter with its
first 34 moments zero forces support exactly 35. -/
theorem full_support_of_filtered_zeros (s : Finset F) (e : F → F)
    (G : Polynomial F) (hs : s.card ≤ 35) (hne : s.Nonempty)
    (he : ∀ x ∈ s, e x ≠ 0) (hx : ∀ x ∈ s, x ≠ 0)
    (hg : ∀ x ∈ s, G.eval x ≠ 0)
    (hz : ∀ k : ℕ, k < 34 →
      (∑ x ∈ s, (e x * x * G.eval x) * x^k) = 0) :
    s.card = 35 := by
  classical
  by_contra hc
  have hcard : s.card ≤ 34 := by omega
  have hf := GVQCC.InvariantPad.moments_injective s
    (fun x => e x * x * G.eval x)
    (fun k hk => hz k (by omega))
  obtain ⟨x, hxs⟩ := hne
  exact (mul_ne_zero (mul_ne_zero (he x hxs) (hx x hxs)) (hg x hxs))
    (hf x hxs)

/-- The 35th filtered moment cannot vanish on a nonempty legal support. -/
theorem filtered_pivot_nonzero (s : Finset F) (e : F → F)
    (G : Polynomial F) (hs : s.card ≤ 35) (hne : s.Nonempty)
    (he : ∀ x ∈ s, e x ≠ 0) (hx : ∀ x ∈ s, x ≠ 0)
    (hg : ∀ x ∈ s, G.eval x ≠ 0)
    (hz : ∀ k : ℕ, k < 34 →
      (∑ x ∈ s, (e x * x * G.eval x) * x^k) = 0) :
    (∑ x ∈ s, (e x * x * G.eval x) * x^34) ≠ 0 := by
  classical
  intro hp
  have hh : ∀ k : ℕ, k < s.card →
      (∑ x ∈ s, (e x * x * G.eval x) * x^k) = 0 := by
    intro k hk
    by_cases h : k < 34
    · exact hz k h
    · have : k = 34 := by omega
      subst k
      exact hp
  have hf := GVQCC.InvariantPad.moments_injective s
    (fun x => e x * x * G.eval x) hh
  obtain ⟨x, hxs⟩ := hne
  exact (mul_ne_zero (mul_ne_zero (he x hxs) (hx x hxs)) (hg x hxs))
    (hf x hxs)

/-- The characteristic-two polynomial identity is written GP+a=HD.
At every root of G, the projective denominator D/a is H inverse. -/
theorem projective_residue (G P H D : Polynomial F) (a x : F)
    (ha : a ≠ 0) (hg : G.eval x = 0)
    (hrel : G * P + C a = H * D) :
    H.eval x * (D.eval x / a) = 1 := by
  have hh := congrArg (fun p : Polynomial F => p.eval x) hrel
  simp [hg] at hh
  rw [← mul_div_assoc, ← hh, div_self ha]

/-- At a locator root the same identity gives the direct magnitude numerator. -/
theorem magnitude_numerator (G P H D : Polynomial F) (a x : F)
    (hd : D.eval x = 0)
    (hrel : G * P = H * D + C a) :
    G.eval x * P.eval x = a := by
  have hh := congrArg (fun p : Polynomial F => p.eval x) hrel
  simpa [hd] using hh

/-- The leading two coordinates of F=D/a can be set without a second
polynomial division. -/
theorem projective_second_coefficient (g q t : F) (h2 : (2 : F) = 0) :
    g*q + (t+q*g) = t := by
  calc
    g*q + (t+q*g) = t + 2*q*g := by ring
    _ = t := by rw [h2, zero_mul, zero_mul, add_zero]

/-- Projective scaling cancels the common nonzero numerator a. -/
theorem projective_magnitude (e x g d f a : F)
    (ha : a ≠ 0) (hf : x*g*f ≠ 0)
    (hd : d = a*f) (hm : e*x*g*d = a) :
    e = (x*g*f)⁻¹ := by
  rw [hd] at hm
  have h : e*(x*g*f)*a = 1*a := by
    calc
      e*(x*g*f)*a = e*x*g*(a*f) := by ring
      _ = a := hm
      _ = 1*a := by ring
  have hh : e*(x*g*f) = 1 := mul_right_cancel₀ ha h
  exact (eq_div_iff hf).2 hh |>.trans (one_div _)

end GVQCC.AllPoleChart

#print axioms GVQCC.AllPoleChart.full_support_of_filtered_zeros
#print axioms GVQCC.AllPoleChart.filtered_pivot_nonzero
#print axioms GVQCC.AllPoleChart.projective_residue
#print axioms GVQCC.AllPoleChart.magnitude_numerator
#print axioms GVQCC.AllPoleChart.projective_second_coefficient
#print axioms GVQCC.AllPoleChart.projective_magnitude
