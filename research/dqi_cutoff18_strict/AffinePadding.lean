import Mathlib
namespace GVQCC.Padding
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



theorem low_degree_obstruction (S : Finset F) (a : F → F) (p : Polynomial F)
    (ha : ∀ x ∈ S, a x ≠ 0) (hx : ∀ x ∈ S, x ≠ 0)
    (hbig : 18 ≤ S.card) (hw : S.card ≤ 35) (hp : p.natDegree ≤ 17)
    (hk : ∀ k : ℕ, k < 35 →
      (∑ x ∈ S, (a x * x * p.eval x) * x^k) = 0) : p = 0 := by
  have hroots : ∀ x ∈ S, p.eval x = 0 := by
    intro x hxs
    have hz := moments_injective S (fun y => a y * y * p.eval y)
      (fun k hk' => hk k (by omega)) x hxs
    exact (mul_eq_zero.mp hz).resolve_left (mul_ne_zero (ha x hxs) (hx x hxs))
  exact Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' p S hroots (by omega)

/-- The union of a low- and high-weight support has at most 52 points.
The first 52 moments therefore distinguish them, without the last 18. -/
theorem moments52_injective (S : Finset F) (a : F → F)
    (hw : S.card ≤ 52) (hx : ∀ x ∈ S, x ≠ 0)
    (hm : ∀ k : ℕ, k < 52 → (∑ x ∈ S, (a x * x) * x^k) = 0) :
    ∀ x ∈ S, a x = 0 := by
  intro x hxs
  have hz := moments_injective S (fun y => a y * y)
    (fun k hk => hm k (by omega)) x hxs
  exact (mul_eq_zero.mp hz).resolve_right (hx x hxs)

/-- Count bound for one padding set: at most one magnitude cancellation
per overlapped support point. -/
theorem padding_weight_bounds (w a c : ℕ) (hw : w ≤ 17)
    (ha : 2*a ≤ w) (hc : c ≤ a) :
    18 ≤ w+18-a-c ∧ w+18-a-c ≤ 35 := by omega

theorem choose_smaller_intersection (w a b : ℕ) (h : a+b ≤ w) :
    2 * min a b ≤ w := by
  by_cases hab : a ≤ b
  · rw [min_eq_left hab]; omega
  · rw [min_eq_right (by omega : b ≤ a)]; omega

theorem disjoint_support_count {α : Type*} [DecidableEq α]
    (E A B : Finset α) (hd : Disjoint A B) :
    (E ∩ A).card + (E ∩ B).card ≤ E.card := by
  have hdis : Disjoint (E ∩ A) (E ∩ B) := by
    rw [Finset.disjoint_left] at hd ⊢
    intro x hx hy
    exact hd (Finset.mem_inter.mp hx).2 (Finset.mem_inter.mp hy).2
  have hs : (E ∩ A) ∪ (E ∩ B) ⊆ E := by
    intro x hx
    rcases Finset.mem_union.mp hx with h | h
    · exact (Finset.mem_inter.mp h).1
    · exact (Finset.mem_inter.mp h).1
  rw [← Finset.card_union_of_disjoint hdis]
  exact Finset.card_le_card hs

theorem affine_padding_phase {A : Type*} [AddCommGroup A]
    (L : A →+ ZMod 2) (e b : A) : L (e+b) + L b = L e := by
  rw [map_add, add_assoc]
  have h (x : ZMod 2) : x+x=0 := by
    calc
      x+x = 2*x := by ring
      _ = 0 := by norm_num
  rw [h,add_zero]

theorem shear_involution (p s : F) (h : (2:F)=0) : (p+s)+s=p := by
  calc
    (p+s)+s=p+2*s := by ring
    _=p := by rw [h,zero_mul,add_zero]

theorem carry_phase_repay (a b m p : Bool) :
    Bool.xor (Bool.xor p (m && a && b)) (m && a && b) = p := by
  cases a <;> cases b <;> cases m <;> cases p <;> decide

end GVQCC.Padding
#print axioms GVQCC.Padding.low_degree_obstruction
#print axioms GVQCC.Padding.moments52_injective
#print axioms GVQCC.Padding.padding_weight_bounds
#print axioms GVQCC.Padding.choose_smaller_intersection
#print axioms GVQCC.Padding.disjoint_support_count
#print axioms GVQCC.Padding.affine_padding_phase
#print axioms GVQCC.Padding.shear_involution
#print axioms GVQCC.Padding.carry_phase_repay
