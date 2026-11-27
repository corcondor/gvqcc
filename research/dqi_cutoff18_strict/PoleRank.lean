import Mathlib

/- Historical peer PoleRank.lean, with the original moment-injectivity proof
   shared verbatim from AffinePadding.lean. Local identities only. -/
namespace GVQCC.PoleRank
open scoped BigOperators
variable {F : Type*} [Field F]

theorem cancel_norm (u ub v b : F) (hzero : u = 0 → ub = 0) :
    (u*ub)*v = b*u^2 ↔ ub*v = b*u := by
  by_cases hu : u = 0
  · simp [hu, hzero hu]
  · constructor
    · intro h
      apply mul_left_cancel₀ hu
      calc
        u*(ub*v) = (u*ub)*v := by ring
        _ = b*u^2 := h
        _ = u*(b*u) := by ring
    · intro h
      calc
        (u*ub)*v = u*(ub*v) := by ring
        _ = u*(b*u) := by rw [h]
        _ = b*u^2 := by ring

theorem shifted_product (u ub v b : F) (hb : b = u+ub) :
    ub*v = b*u ↔ (v+b)*ub = b^2 := by
  have hc : b*u+b*ub = b^2 := by rw [hb]; ring
  constructor
  · intro h
    calc
      (v+b)*ub = ub*v+b*ub := by ring
      _ = b*u+b*ub := by rw [h]
      _ = b^2 := hc
  · intro h
    calc
      ub*v = (v+b)*ub-b*ub := by ring
      _ = b^2-b*ub := by rw [h]
      _ = b*u := by rw [← hc]; ring

theorem hmr_cx_transpose (a b m n : Bool) :
    Bool.xor (m && a) (n && Bool.xor b a) =
      Bool.xor ((Bool.xor m n) && a) (n && b) := by
  cases a <;> cases b <;> cases m <;> cases n <;> decide

theorem hmr_product (a b m p : Bool) :
    Bool.xor (Bool.xor p (m && a && b)) (m && (a && b)) = p := by
  cases a <;> cases b <;> cases m <;> cases p <;> decide

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

theorem recurrence_roots (S : Finset F) (a : F → F) (p : Polynomial F)
    (hs : S.card ≤ 35) (ha : ∀ x ∈ S, a x ≠ 0) (hx : ∀ x ∈ S, x ≠ 0)
    (h : ∀ k : ℕ, k < 35 → (∑ x ∈ S, (a x*x*p.eval x)*x^k) = 0) :
    ∀ x ∈ S, p.eval x = 0 := by
  intro x hxs
  have hz := moments_injective S (fun y => a y*y*p.eval y)
    (fun k hk => h k (lt_of_lt_of_le hk hs)) x hxs
  exact (mul_eq_zero.mp hz).resolve_left (mul_ne_zero (ha x hxs) (hx x hxs))

theorem low_degree_certificate (S : Finset F) (a : F → F) (p : Polynomial F)
    (hs : S.card ≤ 35) (ha : ∀ x ∈ S, a x ≠ 0) (hx : ∀ x ∈ S, x ≠ 0)
    (hp : p ≠ 0) (hd : p.natDegree ≤ 17)
    (h : ∀ k : ℕ, k < 35 → (∑ x ∈ S, (a x*x*p.eval x)*x^k) = 0) :
    S.card ≤ 17 := by
  by_contra hbad
  have hlt : p.natDegree < S.card := by omega
  apply hp
  apply Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' p S _ hlt
  exact recurrence_roots S a p hs ha hx h

theorem tag_recover_budget (w : ℕ) (hw : w ≤ 17) :
    w ≤ 17 ∧ 18 ≤ w+18 ∧ w+18 ≤ 35 := by omega

theorem quadratic_three (a b c x y z : F) (ha : a ≠ 0)
    (hxy : x ≠ y) (hxz : x ≠ z) (hyz : y ≠ z) :
    ¬ (a*x^2+b*x+c = 0 ∧ a*y^2+b*y+c = 0 ∧ a*z^2+b*z+c = 0) := by
  rintro ⟨h1,h2,h3⟩
  have h12 : (x-y)*(a*(x+y)+b) = 0 := by linear_combination h1-h2
  have h13 : (x-z)*(a*(x+z)+b) = 0 := by linear_combination h1-h3
  have q12 := (mul_eq_zero.mp h12).resolve_left (sub_ne_zero.mpr hxy)
  have q13 := (mul_eq_zero.mp h13).resolve_left (sub_ne_zero.mpr hxz)
  have h : a*(y-z) = 0 := by linear_combination q12-q13
  exact (mul_ne_zero ha (sub_ne_zero.mpr hyz)) h

theorem shared_product_shift (u v p q : F) :
    (u+p)*(v+q) - u*v = u*q+p*v+p*q := by ring

end GVQCC.PoleRank
#print axioms GVQCC.PoleRank.cancel_norm
#print axioms GVQCC.PoleRank.shifted_product
#print axioms GVQCC.PoleRank.hmr_cx_transpose
#print axioms GVQCC.PoleRank.hmr_product
#print axioms GVQCC.PoleRank.moments_injective
#print axioms GVQCC.PoleRank.recurrence_roots
#print axioms GVQCC.PoleRank.low_degree_certificate
#print axioms GVQCC.PoleRank.tag_recover_budget
#print axioms GVQCC.PoleRank.quadratic_three
#print axioms GVQCC.PoleRank.shared_product_shift
