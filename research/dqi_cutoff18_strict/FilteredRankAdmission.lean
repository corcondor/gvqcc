import Mathlib

namespace GVQCC.FilteredRank

variable {V W : Type*} [AddCommGroup V] [AddCommGroup W]

/-- Padding is controlled only by a filter-invariant predicate. -/
def pad (F : V →+ W) (p : W → Bool) (g s : V) : V :=
  if p (F s) = true then s + g else s

theorem filter_shift (F : V →+ W) (g s : V) (hg : F g = 0) :
    F (s + g) = F s := by
  rw [map_add, hg, add_zero]

theorem predicate_invariant (F : V →+ W) (p : W → Bool)
    (g s : V) (hg : F g = 0) :
    p (F (s + g)) = p (F s) := by
  rw [filter_shift F g s hg]

theorem pad_preserves_filter (F : V →+ W) (p : W → Bool)
    (g s : V) (hg : F g = 0) :
    F (pad F p g s) = F s := by
  unfold pad
  split
  · exact filter_shift F g s hg
  · rfl

theorem pad_involution (F : V →+ W) (p : W → Bool)
    (g s : V) (hg : F g = 0) (h2 : g + g = 0) :
    pad F p g (pad F p g s) = s := by
  unfold pad
  by_cases h : p (F s) = true
  · have h' : p (F (s + g)) = true := by
      rw [filter_shift F g s hg]
      exact h
    simp only [if_pos h, if_pos h', add_assoc, h2, add_zero]
  · simp only [if_neg h]

/-- A convolution with fixed coefficients rescales each geometric pole.
This is an algebraic lemma, not a native decoder correctness theorem. -/
theorem pole_filter {K : Type*} [Field K] (n i : ℕ)
    (c : Fin n → K) (a x : K) :
    (∑ j : Fin n, c j * (a * x ^ (i + j.val))) =
      (a * x ^ i) * (∑ j : Fin n, c j * x ^ j.val) := by
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro j _
  rw [pow_add]
  ring

/-- Conditional injectivity of the weighted moment map.
The Vandermonde hypothesis is explicit; it is not silently assumed proven. -/
theorem weighted_injective {K : Type*} [Field K] {r : ℕ}
    (x e v : Fin r → K)
    (hsep : ∀ b : Fin r → K,
      (∀ j : Fin r, ∑ k : Fin r, b k * x k ^ j.val = 0) → b = 0)
    (hnz : ∀ k, e k ≠ 0)
    (h : ∀ j : Fin r, ∑ k : Fin r, (e k * v k) * x k ^ j.val = 0) :
    v = 0 := by
  have h0 := hsep (fun k => e k * v k) h
  funext k
  have hh : e k * v k = 0 := congrFun h0 k
  exact (mul_eq_zero.mp hh).resolve_left (hnz k)

theorem padded_degree_bound (w : ℕ) (h : w < 18) :
    w + 18 ≤ 35 := by omega

/-- More selected zero-cost leaves cannot raise the modeled leaf cost.
No assertion of full-circuit phase equivalence is made here. -/
theorem leaf_cost_nonincrease (n old candidate : ℕ) :
    11 * (n - max old candidate) ≤ 11 * (n - old) := by
  have h : old ≤ max old candidate := le_max_left _ _
  omega

/-- The HMR repayment sign is bilinear over Bool. -/
theorem repayment_split (m a b : Bool) :
    (m && (a ^^ b)) = ((m && a) ^^ (m && b)) := by
  cases m <;> cases a <;> cases b <;> decide

#print axioms filter_shift
#print axioms predicate_invariant
#print axioms pad_preserves_filter
#print axioms pad_involution
#print axioms pole_filter
#print axioms weighted_injective
#print axioms padded_degree_bound
#print axioms leaf_cost_nonincrease
#print axioms repayment_split

end GVQCC.FilteredRank
