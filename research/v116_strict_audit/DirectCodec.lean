import Mathlib

namespace GVQCC.V116
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


theorem shifted_kernel_trivial (S : Finset F) (a : F → F)
    (p : Polynomial F) (shift : ℕ)
    (ha : ∀ x ∈ S, a x ≠ 0) (hx : ∀ x ∈ S, x ≠ 0)
    (hp : p.natDegree < S.card)
    (hk : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, (a x * x^shift * p.eval x) * x^k) = 0) : p = 0 := by
  apply Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' p S _ hp
  intro x hxs
  have hz := moments_injective S (fun y => a y * y^shift * p.eval y) hk x hxs
  exact (mul_eq_zero.mp hz).resolve_left (mul_ne_zero (ha x hxs) (pow_ne_zero _ (hx x hxs)))

theorem moment_expansion (S : Finset F) (J : Finset ℕ) (v : ℕ → F) (k : ℕ) :
    (∑ x ∈ S, ((∑ j ∈ J, v j * x^j) * x^k)) =
      ∑ j ∈ J, v j * (∑ x ∈ S, x^(j+k)) := by
  classical
  calc
    _ = ∑ x ∈ S, ∑ j ∈ J, v j * x^(j+k) := by
      apply Finset.sum_congr rfl
      intro x _
      rw [Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro j _
      rw [pow_add]
      ring
    _ = ∑ j ∈ J, ∑ x ∈ S, v j * x^(j+k) := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro j _
      rw [Finset.mul_sum]

theorem magnitude_at_simple_root (x d n e : F)
    (hx : x ≠ 0) (hd : d ≠ 0) (hn : n = e * (x*d)) : n / (x*d) = e := by
  rw [hn, mul_div_cancel_right₀ _ (mul_ne_zero hx hd)]

theorem singular_chart (n d h : F) (hn : n = 0) (hd : d ≠ 0) : d - h*n ≠ 0 := by
  simpa [hn] using hd

theorem triangular_step_inverse (s t : F) : (s+t)-t=s := by ring

theorem pair_cross (a b c d : ZMod 2) : (a+b)*(c+d)+a*c+b*d=a*d+b*c := by
  have h (x : ZMod 2) : x+x=0 := by
    have h2 : (2 : ZMod 2)=0 := by decide
    calc x+x = 2*x := by ring
         _ = 0 := by rw [h2, zero_mul]
  calc
    _ = (a*c+a*c)+(b*d+b*d)+a*d+b*c := by ring
    _ = _ := by rw [h, h]; ring

/-- A single field word cannot distinguish the ordinary zero quotient and the pole code. -/
noncomputable def encodeHead (n d : F) : F := by
  classical
  exact if n = 0 then 0 else d / n

theorem zero_head_collision : encodeHead (0 : F) 1 = encodeHead 1 0 := by
  classical
  simp [encodeHead]

/-- With an incoming unit denominator, the compressed head identifies the pole. -/
theorem head_zero_iff (n d : F) (hd : d ≠ 0) : encodeHead n d = 0 ↔ n = 0 := by
  classical
  by_cases hn : n = 0
  · simp [encodeHead, hn]
  · simp [encodeHead, hn, div_ne_zero hd hn]

end GVQCC.V116
#print axioms GVQCC.V116.shifted_kernel_trivial
#print axioms GVQCC.V116.moment_expansion
#print axioms GVQCC.V116.magnitude_at_simple_root
#print axioms GVQCC.V116.singular_chart
#print axioms GVQCC.V116.triangular_step_inverse
#print axioms GVQCC.V116.pair_cross
#print axioms GVQCC.V116.zero_head_collision
#print axioms GVQCC.V116.head_zero_iff
