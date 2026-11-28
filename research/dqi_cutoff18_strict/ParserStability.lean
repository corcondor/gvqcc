import Mathlib.Algebra.Field.Basic
import Lean.Elab.Tactic.Omega

/-!
The first-nonzero selector used by `infinity_cf.py:span` is stable under
reciprocal updates of the selected suffix: the prefix is unchanged, the
first nonzero coefficient is inverted, and subsequent coefficients may
change arbitrarily. This proves a concrete selector property rather than
assuming `tag (T (tag x) x) = tag x`.

Scope: word-level first-nonzero scan and the remaining-precision guard.
This file does not certify GF(4096) bit packing, native KMB gate semantics,
the complete boundary counter, the series reciprocal, or the DQI oracle.
-/

namespace GVQCC.ParserStability

variable {F : Type*} [Field F]

/-- Bounded first-nonzero scan, with an absolute word index. -/
noncomputable def firstNonzero (s : ℕ → F) (i : ℕ) : ℕ → Option ℕ := by
  classical
  exact fun
    | 0 => none
    | n + 1 => if s i = 0 then firstNonzero s (i + 1) n else some i

theorem firstNonzero_lower (s : ℕ → F) (i n p : ℕ)
    (h : firstNonzero s i n = some p) : i ≤ p := by
  classical
  induction n generalizing i with
  | zero => simp [firstNonzero] at h
  | succ n ih =>
    by_cases hz : s i = 0
    · have ht : firstNonzero s (i + 1) n = some p := by
        simpa [firstNonzero, hz] using h
      have := ih (i + 1) ht
      omega
    · have hp : i = p := by simpa [firstNonzero, hz] using h
      omega

theorem firstNonzero_nonzero (s : ℕ → F) (i n p : ℕ)
    (h : firstNonzero s i n = some p) : s p ≠ 0 := by
  classical
  induction n generalizing i with
  | zero => simp [firstNonzero] at h
  | succ n ih =>
    by_cases hz : s i = 0
    · exact ih (i + 1) (by simpa [firstNonzero, hz] using h)
    · have hp : i = p := by simpa [firstNonzero, hz] using h
      simpa [← hp] using hz

/-- Only zero/nonzero tests through the selected pivot affect the scan. -/
theorem firstNonzero_prefix_stable (s t : ℕ → F) (i n p : ℕ)
    (h : firstNonzero s i n = some p)
    (hz : ∀ j, i ≤ j → j ≤ p → (t j = 0 ↔ s j = 0)) :
    firstNonzero t i n = some p := by
  classical
  induction n generalizing i with
  | zero => simp [firstNonzero] at h
  | succ n ih =>
    have hip := firstNonzero_lower s i (n + 1) p h
    by_cases hs : s i = 0
    · have ht : t i = 0 := (hz i (by omega) hip).mpr hs
      have hh : firstNonzero s (i + 1) n = some p := by
        simpa [firstNonzero, hs] using h
      have htail : firstNonzero t (i + 1) n = some p :=
        ih (i + 1) hh (fun j hj hjp => hz j (by omega) hjp)
      simpa [firstNonzero, ht] using htail
    · have ht : t i ≠ 0 := by
        intro hti
        exact hs ((hz i (by omega) hip).mp hti)
      simpa [firstNonzero, hs, ht] using h

/-- The observable shape of a reciprocal suffix update. Its suffix is
unrestricted because the first-nonzero scan stops at `p`. -/
noncomputable def reciprocalSuffix (s tail : ℕ → F) (p : ℕ) (j : ℕ) : F :=
  if j < p then s j else if j = p then (s p)⁻¹ else tail j

theorem reciprocalSuffix_zero_iff (s tail : ℕ → F) (p j : ℕ)
    (hj : j ≤ p) : reciprocalSuffix s tail p j = 0 ↔ s j = 0 := by
  classical
  by_cases hlt : j < p
  · simp [reciprocalSuffix, hlt]
  · have he : j = p := by omega
    subst j
    simp [reciprocalSuffix]

theorem firstNonzero_reciprocal_stable (s tail : ℕ → F) (i n p : ℕ)
    (h : firstNonzero s i n = some p) :
    firstNonzero (reciprocalSuffix s tail p) i n = some p := by
  exact firstNonzero_prefix_stable s (reciprocalSuffix s tail p) i n p h
    (fun j _ hj => reciprocalSuffix_zero_iff s tail p j hj)

/-- `span` returns the block degree only when twice that degree fits in
the remaining words, as in the Python reference. -/
noncomputable def span (s : ℕ → F) (i n : ℕ) : Option ℕ := do
  let p ← firstNonzero s i n
  let d := p + 1 - i
  if 2 * d ≤ n then some d else none

theorem span_reciprocal_stable (s tail : ℕ → F) (i n p : ℕ)
    (h : firstNonzero s i n = some p) :
    span (reciprocalSuffix s tail p) i n = span s i n := by
  have ht := firstNonzero_reciprocal_stable s tail i n p h
  simp [span, h, ht]

/-- The reciprocal shape can itself be read off an implemented word map:
an unchanged prefix and inverted head suffice; there is no hypothesis on
the words strictly after the head. -/
theorem firstNonzero_of_reciprocal_shape (s t : ℕ → F) (i n p : ℕ)
    (h : firstNonzero s i n = some p)
    (hprefix : ∀ j, j < p → t j = s j)
    (hhead : t p = (s p)⁻¹) :
    firstNonzero t i n = some p := by
  apply firstNonzero_prefix_stable s t i n p h
  intro j _ hj
  by_cases hlt : j < p
  · rw [hprefix j hlt]
  · have he : j = p := by omega
    subst j
    rw [hhead]
    exact inv_eq_zero

/-- A local involution with reciprocal head shape preserves its concrete
guard in both directions, including data for which this guard is false. -/
theorem reciprocal_guard_iff (T : (ℕ → F) → (ℕ → F))
    (hT : Function.Involutive T) (i n p : ℕ)
    (hprefix : ∀ s j, j < p → T s j = s j)
    (hhead : ∀ s, T s p = (s p)⁻¹) (s : ℕ → F) :
    firstNonzero (T s) i n = some p ↔ firstNonzero s i n = some p := by
  constructor
  · intro h
    have hh := firstNonzero_of_reciprocal_shape (T s) (T (T s)) i n p h
      (hprefix (T s)) (hhead (T s))
    simpa [hT s] using hh
  · intro h
    exact firstNonzero_of_reciprocal_shape s (T s) i n p h
      (hprefix s) (hhead s)

noncomputable def guardedReciprocal (T : (ℕ → F) → (ℕ → F))
    (i n p : ℕ) (s : ℕ → F) : ℕ → F := by
  classical
  exact if firstNonzero s i n = some p ∧ 2 * (p + 1 - i) ≤ n then T s else s

/-- Concrete span-controlled local step is reversible without storing its
guard. The series-update involution itself remains a separate obligation. -/
theorem guardedReciprocal_involutive (T : (ℕ → F) → (ℕ → F))
    (i n p : ℕ) (hT : ∀ s, s p ≠ 0 → T (T s) = s)
    (hprefix : ∀ s j, j < p → T s j = s j)
    (hhead : ∀ s, T s p = (s p)⁻¹) :
    Function.Involutive (guardedReciprocal T i n p) := by
  classical
  intro s
  by_cases h : firstNonzero s i n = some p ∧ 2 * (p + 1 - i) ≤ n
  · have ht : firstNonzero (T s) i n = some p ∧ 2 * (p + 1 - i) ≤ n :=
      ⟨firstNonzero_of_reciprocal_shape s (T s) i n p h.1
        (hprefix s) (hhead s), h.2⟩
    simp only [guardedReciprocal, ite_eq_left h, ite_eq_left ht]
    exact hT s (firstNonzero_nonzero s i n p h.1)
  · simp only [guardedReciprocal, ite_eq_right h]

end GVQCC.ParserStability

#print axioms GVQCC.ParserStability.firstNonzero_lower
#print axioms GVQCC.ParserStability.firstNonzero_nonzero
#print axioms GVQCC.ParserStability.firstNonzero_prefix_stable
#print axioms GVQCC.ParserStability.reciprocalSuffix_zero_iff
#print axioms GVQCC.ParserStability.firstNonzero_reciprocal_stable
#print axioms GVQCC.ParserStability.span_reciprocal_stable
#print axioms GVQCC.ParserStability.firstNonzero_of_reciprocal_shape
#print axioms GVQCC.ParserStability.reciprocal_guard_iff
#print axioms GVQCC.ParserStability.guardedReciprocal_involutive
