import InvariantPad
namespace GVQCC.SparseSyndromeGuard
open scoped BigOperators
variable {F : Type*} [Field F]

/-- Exact 70-moment uniqueness on nonzero-root supports. The DQI moments
    begin at exponent k+1, unlike the base lemma in InvariantPad.lean. -/
theorem nonzero_support_moments_injective (s : Finset F) (a : F → F)
    (hs : s.card ≤ 70) (hx : ∀ x ∈ s, x ≠ 0)
    (hmom : ∀ k : ℕ, k < 70 →
       (∑ x ∈ s, a x * x^(k+1)) = 0) :
    ∀ x ∈ s, a x = 0 := by
  classical
  have hm : ∀ k : ℕ, k < s.card →
      (∑ x ∈ s, (a x * x) * x^k) = 0 := by
    intro k hk
    calc
      (∑ x ∈ s, (a x * x) * x^k) =
          (∑ x ∈ s, a x * x^(k+1)) := by
        apply Finset.sum_congr rfl
        intro x _
        rw [pow_succ]
        ring
      _ = 0 := hmom k (by omega)
  have hz := GVQCC.InvariantPad.moments_injective s (fun x => a x * x) hm
  intro x hxs
  exact (mul_eq_zero.mp (hz x hxs)).resolve_right (hx x hxs)

/-- Two supported legal syndromes have union support of size at most 70. -/
theorem union_card_le_70 {α : Type*} [DecidableEq α] (s t : Finset α)
    (hs : s.card ≤ 35) (ht : t.card ≤ 35) : (s ∪ t).card ≤ 70 := by
  calc
    (s ∪ t).card ≤ s.card + t.card := Finset.card_union_le s t
    _ ≤ 70 := by omega

/-- A 70-word agreement certificate forces the original two sparse
    input syndromes to coincide. An arbitrary corrupt output has no such
    certificate unless ORIGINAL input equality is separately checked. -/
theorem sparse_difference_zero [DecidableEq F] (s t : Finset F) (a b : F → F)
    (hs : s.card ≤ 35) (ht : t.card ≤ 35)
    (hnz : ∀ x ∈ s ∪ t, x ≠ 0)
    (hmom : ∀ k : ℕ, k < 70 →
      (∑ x ∈ s ∪ t,
        ((if x ∈ s then a x else 0) - (if x ∈ t then b x else 0)) * x^(k+1)) = 0) :
    ∀ x ∈ s ∪ t, (if x ∈ s then a x else 0) =
                     (if x ∈ t then b x else 0) := by
  intro x hx
  have h := nonzero_support_moments_injective (s ∪ t)
      (fun y => (if y ∈ s then a y else 0) - (if y ∈ t then b y else 0))
      (union_card_le_70 s t hs ht) hnz hmom x hx
  exact sub_eq_zero.mp h

/-- The cross term of finite-difference transport cannot be dropped. -/
theorem finite_difference_product (a b da db : Bool) :
    Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
      Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

/-- If the true input has at most 35 distinct nonzero support points and the
    candidate has at most r, just 35+r ORIGINAL input moments suffice.
    This is a tighter proof obligation than verifying all 70 words.
    It does NOT justify comparing to a corrupted donor output instead. -/
theorem sparse_35_vs_r_unique [DecidableEq F] (s t : Finset F) (a b : F → F) (r : ℕ)
    (hs : s.card ≤ 35) (ht : t.card ≤ r)
    (hnz : ∀ x ∈ s ∪ t, x ≠ 0)
    (hmom : ∀ k : ℕ, k < 35 + r →
      (∑ x ∈ s ∪ t,
        ((if x ∈ s then a x else 0) - (if x ∈ t then b x else 0)) * x^(k+1)) = 0) :
    ∀ x ∈ s ∪ t, (if x ∈ s then a x else 0) =
                     (if x ∈ t then b x else 0) := by
  classical
  let d : F → F := fun x =>
    (if x ∈ s then a x else 0) - (if x ∈ t then b x else 0)
  have hcard : (s ∪ t).card ≤ 35 + r := by
    calc
      (s ∪ t).card ≤ s.card + t.card := Finset.card_union_le s t
      _ ≤ 35 + r := by omega
  have hh : ∀ k : ℕ, k < (s ∪ t).card →
      (∑ x ∈ s ∪ t, (d x * x) * x^k) = 0 := by
    intro k hk
    calc
      (∑ x ∈ s ∪ t, (d x * x) * x^k) =
          (∑ x ∈ s ∪ t, d x * x^(k+1)) := by
        apply Finset.sum_congr rfl
        intro x _
        rw [pow_succ]
        ring
      _ = 0 := hmom k (by omega)
  have hzero := GVQCC.InvariantPad.moments_injective
    (s ∪ t) (fun x => d x * x) hh
  intro x hx
  have hdx : d x = 0 :=
    (mul_eq_zero.mp (hzero x hx)).resolve_right (hnz x hx)
  exact sub_eq_zero.mp hdx


end GVQCC.SparseSyndromeGuard
#print axioms GVQCC.SparseSyndromeGuard.nonzero_support_moments_injective
#print axioms GVQCC.SparseSyndromeGuard.union_card_le_70
#print axioms GVQCC.SparseSyndromeGuard.sparse_difference_zero
#print axioms GVQCC.SparseSyndromeGuard.finite_difference_product
#print axioms GVQCC.SparseSyndromeGuard.sparse_35_vs_r_unique
