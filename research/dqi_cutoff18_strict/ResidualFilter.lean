import Mathlib
namespace GVQCC.ResidualFilter
open scoped BigOperators
variable {F : Type*} [Field F]

theorem moments_injective (s : Finset F) (a : F → F)
    (h : ∀ k : ℕ, k < s.card → (∑ x ∈ s, a x * x^k) = 0) :
    ∀ x ∈ s, a x = 0 := by
  classical
  induction s using Finset.induction_on generalizing a with
  | empty => simp
  | @insert b s hb ih =>
    have hs : ∀ k : ℕ, k < s.card →
        (∑ y ∈ s, (a y * (y-b))*y^k) = 0 := by
      intro k hk
      have h0 := h k (by rw [Finset.card_insert_of_notMem hb]; omega)
      have h1 := h (k+1) (by rw [Finset.card_insert_of_notMem hb]; omega)
      rw [Finset.sum_insert hb] at h0 h1
      calc
        (∑ y ∈ s, (a y * (y-b))*y^k) =
            (∑ y ∈ s, a y * y^(k+1)) - b*(∑ y ∈ s, a y * y^k) := by
          rw [Finset.mul_sum, ← Finset.sum_sub_distrib]
          apply Finset.sum_congr rfl
          intro y _
          rw [pow_succ]
          ring
        _ = 0 := by
          rw [pow_succ b] at h1
          linear_combination h1 - b*h0
    have hz := ih (fun y => a y*(y-b)) hs
    have hrest : ∀ x ∈ s, a x = 0 := by
      intro x hx
      have hne : x-b ≠ 0 := sub_ne_zero.mpr (by
        intro he
        subst x
        exact hb hx)
      exact (mul_eq_zero.mp (hz x hx)).resolve_right hne
    have hsum : (∑ x ∈ s, a x*x^0) = 0 := Finset.sum_eq_zero
      (fun x hx => by simp [hrest x hx])
    have h0 := h 0 (by rw [Finset.card_insert_of_notMem hb]; omega)
    rw [Finset.sum_insert hb, hsum] at h0
    have hab : a b = 0 := by simpa using h0
    intro x hx
    rcases Finset.mem_insert.mp hx with rfl | hx
    · exact hab
    · exact hrest x hx

/-- Filtering finite-field moments by polynomial coefficients scales each
nonzero locator's magnitude by the polynomial evaluation. -/
theorem filter_moment (S : Finset F) (a : F → F) (J : Finset ℕ)
    (p : ℕ → F) (i : ℕ) :
    (∑ j ∈ J, p j * (∑ x ∈ S, a x * x^(i+j+1))) =
      ∑ x ∈ S, (a x * (∑ j ∈ J, p j * x^j)) * x^(i+1) := by
  classical
  calc
    _ = ∑ j ∈ J, ∑ x ∈ S, p j * (a x * x^(i+j+1)) := by
      simp_rw [Finset.mul_sum]
    _ = ∑ x ∈ S, ∑ j ∈ J, p j * (a x * x^(i+j+1)) := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro x _
      rw [Finset.mul_sum, Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro j _
      rw [show i+j+1 = (i+1)+j by omega, pow_add]
      ring

/-- Union support of at most 2w, with nonvanishing filter on that support.
The first |S| filtered moments uniquely determine the magnitudes. -/
theorem filter_kernel_trivial (S : Finset F) (a p : F → F)
    (hx : ∀ x ∈ S, x ≠ 0) (hp : ∀ x ∈ S, p x ≠ 0)
    (hm : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, (a x * p x) * x^(k+1)) = 0) :
    ∀ x ∈ S, a x = 0 := by
  have hm' : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, (a x * p x * x) * x^k) = 0 := by
    intro k hk
    calc
      _ = ∑ x ∈ S, (a x * p x) * x^(k+1) := by
        apply Finset.sum_congr rfl
        intro x _
        rw [pow_succ]
        ring
      _ = 0 := hm k hk
  intro x hxs
  have hz := moments_injective S (fun x => a x * p x * x) hm' x hxs
  exact (mul_eq_zero.mp ((mul_eq_zero.mp hz).resolve_right (hx x hxs))).resolve_right (hp x hxs)

/-- Subtraction of two candidate sparse syndromes on the union support. -/
theorem filter_unique (S : Finset F) (a b p : F → F)
    (hx : ∀ x ∈ S, x ≠ 0) (hp : ∀ x ∈ S, p x ≠ 0)
    (hm : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, (a x * p x) * x^(k+1)) =
      (∑ x ∈ S, (b x * p x) * x^(k+1))) :
    ∀ x ∈ S, a x = b x := by
  have hd : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, ((a x-b x) * p x) * x^(k+1)) = 0 := by
    intro k hk
    simp_rw [sub_mul, Finset.sum_sub_distrib]
    rw [hm k hk, sub_self]
  intro x hs
  exact sub_eq_zero.mp (filter_kernel_trivial S (fun x => a x-b x) p hx hp hd x hs)

/-- One triangular row update has an exact inverse in characteristic two. -/
theorem row_involution (x y : F) (h : (2:F)=0) : (x+y)+y=x := by
  calc
    (x+y)+y=x+2*y := by ring
    _=x := by rw [h,zero_mul,add_zero]

end GVQCC.ResidualFilter
#print axioms GVQCC.ResidualFilter.moments_injective
#print axioms GVQCC.ResidualFilter.filter_moment
#print axioms GVQCC.ResidualFilter.filter_kernel_trivial
#print axioms GVQCC.ResidualFilter.filter_unique
#print axioms GVQCC.ResidualFilter.row_involution
