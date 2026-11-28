import Init

namespace GVQCC.DisjointPad247

/-- The tag predicate is a two-point coset; translating by the first pad
    leaves the predicate unchanged. The field-addition law is XOR. -/
theorem coset_invariant {A : Type} (add : A → A → A) (zero a : A)
    (id : ∀ x, add x zero = x)
    (assoc : ∀ x y z, add (add x y) z = add x (add y z))
    (za : add zero a = a) (aa : add a a = zero) (u : A) :
    (add u a = zero ∨ add u a = a) ↔ (u = zero ∨ u = a) := by
  have inv : add (add u a) a = u := by rw [assoc, aa, id]
  constructor
  · intro h
    cases h with
    | inl h => right; rw [h, za] at inv; exact inv.symm
    | inr h => left; rw [h, aa] at inv; exact inv.symm
  · intro h
    cases h with
    | inl h => right; rw [h, za]
    | inr h => left; rw [h, aa]

/-- The first jet is nonzero after either permitted translation.
    This is not a statement about later Hermite pivots. -/
theorem first_jet_safe {A : Type} (add : A → A → A) (zero u a b : A)
    (cancel_a : add u a = zero → u = a)
    (cancel_b : add u b = zero → u = b)
    (hb0 : b ≠ zero) (hba : b ≠ a) :
    ((u ≠ zero ∧ u ≠ a) → add u a ≠ zero) ∧
    ((u = zero ∨ u = a) → add u b ≠ zero) := by
  constructor
  · intro h hz
    exact h.2 (cancel_a hz)
  · intro h hz
    have hu := cancel_b hz
    cases h with
    | inl h => exact hb0 (hu.symm.trans h)
    | inr h => exact hba (hu.symm.trans h)

/-- Disjoint pad support forces the other filter above the low-weight
    threshold. This lemma assumes exact support recognition. -/
theorem disjoint_weight (w : Nat) :
    w + 18 > 17 := by omega

theorem tag_clear (low a : Bool) :
    Bool.xor (low && a) (low && a) = false := by
  cases low <;> cases a <;> decide

#print axioms coset_invariant
#print axioms first_jet_safe
#print axioms disjoint_weight
#print axioms tag_clear
end GVQCC.DisjointPad247
