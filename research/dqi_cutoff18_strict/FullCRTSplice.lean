import Mathlib

namespace GVQCC.FullCRTSplice
open scoped BigOperators

/-- All 70 moments commute with any field homomorphism, including Frobenius. -/
theorem moment_transport {F K I : Type*} [Field F] [Field K]
    (f : F →+* K) (s : Finset I) (e x : I → F) (j : ℕ) :
    f (∑ i ∈ s, e i * x i ^ (j+1)) =
      ∑ i ∈ s, f (e i) * f (x i) ^ (j+1) := by
  simp only [map_sum, map_mul, map_pow]

/-- This ratio is the exact transfer from the G-chart phase scan to the
single-pole numerator A, with U=G^2 and nonzero derivative at a root. -/
theorem mask_ratio {F : Type*} [Field F] (a g d : F)
    (hg : g ≠ 0) (hd : d ≠ 0) :
    a / (g^2*d) = (a/g) * (1/(g*d)) := by
  field_simp

/-- A fixed invertible coordinate change transports, rather than removes,
the error set. The inverse image of any value counterexample is a counterexample. -/
theorem conjugation_counterexample {A : Type*} (f : A ≃ A) (u : A → A)
    (x : A) (h : u x ≠ x) : f.symm (u (f (f.symm x))) ≠ f.symm x := by
  rw [Equiv.apply_symm_apply]
  intro h'
  exact h (f.symm.injective h')

/-- Two-sided reversible transport of the correct phase-only operation. -/
theorem phase_transport {A B : Type*} (f : A ≃ B) (p : B → Bool) (x : A) :
    (f.symm (f x), p (f x)) = (x, p (f x)) := by
  simp

/-- If a pairing is contravariant under the chosen dual mask map,
each individual phase summand is preserved. -/
theorem dual_mask_transport {A M : Type*} (f : A ≃ A) (d : M → M)
    (p : M → A → Bool) (h : ∀ m e, p (d m) (f e) = p m e)
    (m : M) (e : A) : p (d m) (f e) = p m e := h m e

theorem hmr_repayment (phase m x : Bool) :
    (phase ^^ (m && x)) ^^ (m && x) = phase := by
  cases phase <;> cases m <;> cases x <;> decide

end GVQCC.FullCRTSplice

#print axioms GVQCC.FullCRTSplice.moment_transport
#print axioms GVQCC.FullCRTSplice.mask_ratio
#print axioms GVQCC.FullCRTSplice.conjugation_counterexample
#print axioms GVQCC.FullCRTSplice.phase_transport
#print axioms GVQCC.FullCRTSplice.dual_mask_transport
#print axioms GVQCC.FullCRTSplice.hmr_repayment
