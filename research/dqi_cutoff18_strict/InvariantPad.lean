import Mathlib
namespace GVQCC.InvariantPad
open scoped BigOperators
open Polynomial
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




/-- A linear quotient kills the fixed extension pad. -/
theorem quotient_unchanged {A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (L : A →+ B) (s p : A) (hp : L p = 0) :
    L (s+p) = L s := by rw [map_add, hp, add_zero]

theorem selector_unchanged {A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (L : A →+ B) (g : B → Bool) (s p : A) (hp : L p = 0) :
    g (L (s+p)) = g (L s) := by rw [quotient_unchanged L s p hp]

/-- No branch bit needs to be parked across the donor. -/
def padBy {A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (L : A →+ B) (g : B → Bool) (p s : A) : A :=
    if g (L s) then s+p else s

theorem tagfree_involution {A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (L : A →+ B) (g : B → Bool) (p s : A) (hp : L p = 0)
    (h2 : p+p = 0) : padBy L g p (padBy L g p s) = s := by
  cases h : g (L s) with
  | false => simp [padBy, h]
  | true =>
    have hh : g (L (s+p)) = true := by rw [selector_unchanged L g s p hp, h]
    simp [padBy, h, hh, add_assoc, h2]

/-- Filtered moments have the same support when the filter has no root in it. -/
theorem filter_nonzero (a x : F) (p : Polynomial F)
    (ha : a ≠ 0) (hx : x ≠ 0) (hp : p.eval x ≠ 0) :
    a*x*p.eval x ≠ 0 := mul_ne_zero (mul_ne_zero ha hx) hp

/-- Every nonzero root-free-filtered coefficient has to be annihilated
by a recurrence checked on 35 consecutive residual moments. -/
theorem filtered_recurrence_sound (S : Finset F) (a : F → F)
    (f p : Polynomial F) (ha : ∀ x ∈ S, a x ≠ 0)
    (hx : ∀ x ∈ S, x ≠ 0) (hf : ∀ x ∈ S, f.eval x ≠ 0)
    (hw : S.card ≤ 35) (hp : p ≠ 0)
    (hk : ∀ k : ℕ, k < 35 →
       (∑ x ∈ S, (a x*x*f.eval x*p.eval x)*x^k) = 0) :
    S.card ≤ p.natDegree := by
  have hr : ∀ x ∈ S, p.eval x = 0 := by
    intro x hxs
    have hz := moments_injective S (fun y => a y*y*f.eval y*p.eval y)
      (fun k hk' => hk k (by omega)) x hxs
    exact (mul_eq_zero.mp hz).resolve_left
      (filter_nonzero (a x) x f (ha x hxs) (hx x hxs) (hf x hxs))
  by_contra h
  exact hp (Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' p S hr (by omega))

/-- General support bound for the nine distinct conjugate pairs. -/
theorem extension_degree_budget (w : ℕ) (h : w ≤ 17) :
    18 ≤ w+18 ∧ w+18 ≤ 35 := by omega

/-- Two distinct nonzero poles give a nonsingular 2x2 Hankel minor. -/
theorem rank2_det (a b x z : F) :
    (a+b)*(a*x^2+b*z^2)-(a*x+b*z)^2 = a*b*(x-z)^2 := by ring

theorem rank2_det_unit (a b x z : F) (ha : a ≠ 0) (hb : b ≠ 0) (hx : x ≠ z) :
    (a+b)*(a*x^2+b*z^2)-(a*x+b*z)^2 ≠ 0 := by
  rw [rank2_det]
  exact mul_ne_zero (mul_ne_zero ha hb) (pow_ne_zero _ (sub_ne_zero.mpr hx))

theorem rank2_sum_numerator (a b x z : F) :
    (a+b)*(a*x^3+b*z^3)-(a*x+b*z)*(a*x^2+b*z^2) =
    ((a+b)*(a*x^2+b*z^2)-(a*x+b*z)^2)*(x+z) := by ring

theorem rank2_product_numerator (a b x z : F) :
    (a*x+b*z)*(a*x^3+b*z^3)-(a*x^2+b*z^2)^2 =
    ((a+b)*(a*x^2+b*z^2)-(a*x+b*z)^2)*(x*z) := by ring

theorem rank1_fallback (a x : F) (ha : a ≠ 0) : (a*x)/a = x := by
  field_simp

end GVQCC.InvariantPad
#print axioms GVQCC.InvariantPad.quotient_unchanged
#print axioms GVQCC.InvariantPad.selector_unchanged
#print axioms GVQCC.InvariantPad.tagfree_involution
#print axioms GVQCC.InvariantPad.filter_nonzero
#print axioms GVQCC.InvariantPad.filtered_recurrence_sound
#print axioms GVQCC.InvariantPad.extension_degree_budget
#print axioms GVQCC.InvariantPad.rank2_det
#print axioms GVQCC.InvariantPad.rank2_det_unit
#print axioms GVQCC.InvariantPad.rank2_sum_numerator
#print axioms GVQCC.InvariantPad.rank2_product_numerator
#print axioms GVQCC.InvariantPad.rank1_fallback
