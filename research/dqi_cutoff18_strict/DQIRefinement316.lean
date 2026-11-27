import Mathlib
import InvariantPad

namespace GVQCC.DQIRefinement316

open scoped BigOperators
variable {F : Type*} [Field F]

/-- DQI has 70 moments beginning at exponent one, not exponent zero.
The two sparse candidates are extended by zero to the union support. -/
def moments (S : Finset F) (a : F → F) (k : ℕ) : F :=
  ∑ x ∈ S, (a x*x)*x^k

/-- Any two candidates with combined support ≤70 and nonzero nodes that
agree on the 70 syndrome words have identical magnitudes on the union.
This reuses the existing Vandermonde theorem, without any decoder hypothesis. -/
theorem sparse_unique70 (S : Finset F) (a b : F → F)
    (hS : S.card ≤ 70) (hx : ∀ x ∈ S, x ≠ 0)
    (hm : ∀ k : ℕ, k < 70 → moments S a k = moments S b k) :
    ∀ x ∈ S, a x = b x := by
  have hv : ∀ k : ℕ, k < S.card →
      (∑ x ∈ S, ((a x-b x)*x)*x^k) = 0 := by
    intro k hk
    have h := hm k (by omega)
    unfold moments at h
    calc
      _ = (∑ x ∈ S, (a x*x)*x^k) - (∑ x ∈ S, (b x*x)*x^k) := by
        rw [← Finset.sum_sub_distrib]
        apply Finset.sum_congr rfl
        intro x _
        ring
      _ = 0 := sub_eq_zero.mpr h
  intro x hxs
  have hz := GVQCC.InvariantPad.moments_injective S
      (fun y => (a y-b y)*y) hv x hxs
  exact sub_eq_zero.mp ((mul_eq_zero.mp hz).resolve_right (hx x hxs))

/-- Phase target: the binary dot product of the recovered magnitude and
the supplied classical mask. No field trace/basis substitution assumed. -/
def phaseTarget (n : ℕ) (e m : ℕ → Bool) : Bool :=
  (List.range n).foldl (fun p j => Bool.xor p (e j && m j)) false

theorem phaseTarget_congr (n : ℕ) (e f m : ℕ → Bool)
    (h : ∀ j, e j = f j) : phaseTarget n e m = phaseTarget n f m := by
  have he : e = f := funext h
  rw [he]

/-- At each HMR site the bit value x is removed, and the measured
outcome r contributes phase r*x; compensation must use that exact value. -/
theorem hmr_exact (p r x a b : Bool) (h : x = (a && b)) :
    Bool.xor (Bool.xor p (r && x)) (r && (a && b)) = p := by
  subst x
  cases p <;> cases r <;> cases a <;> cases b <;> rfl

/-- Conversely, a wrong product witness cannot repay both outcomes. -/
theorem hmr_necessary (x a b : Bool)
    (h : ∀ r : Bool, Bool.xor (r && x) (r && (a && b)) = false) :
    x = (a && b) := by
  have hh := h true
  cases x <;> cases a <;> cases b <;> simp_all

/-- Compositional statement in the basis/phase semantics of KickMix.
q and c include ALL physical quantum and classical bits. Outcome histories
are explicit parameters, not sampled hypotheses. -/
structure State where
  q : ℕ → Bool
  c : ℕ → Bool
  phase : Bool

def withPhase (s : State) (p : Bool) : State := ⟨s.q,s.c,p⟩

def CorrectOracle (run : State → State) (s : State) (p : Bool) : Prop :=
  (run s).q = s.q ∧ (run s).c = s.c ∧ (run s).phase = Bool.xor s.phase p

/-- The entire compute/scan/uncompute contract, for any legal input and
any paired measurement history satisfying the three concrete seam obligations.
The seam obligations must be discharged for the actual emitted physical tape. -/
theorem oracle_compose (C P U : State → State) (s : State) (p : Bool)
    (hC : (C s).phase = s.phase)
    (hPq : (P (C s)).q = (C s).q)
    (hPc : (P (C s)).c = (C s).c)
    (hPp : (P (C s)).phase = Bool.xor (C s).phase p)
    (hU : ∀ z : Bool, U (withPhase (C s) z) = withPhase s z) :
    CorrectOracle (fun x => U (P (C x))) s p := by
  have hstate : P (C s) = withPhase (C s) (Bool.xor s.phase p) := by
    cases h : P (C s) with
    | mk q c phase =>
      simp only [h] at hPq hPc hPp
      simp only [withPhase, hPq, hPc, hPp, hC]
  change (U (P (C s))).q = s.q ∧
      (U (P (C s))).c = s.c ∧ (U (P (C s))).phase = Bool.xor s.phase p
  rw [hstate, hU]
  exact ⟨rfl,rfl,rfl⟩

/-- A sampled value mismatch is a logically decisive counterexample to
universal refinement; zero sampled mismatches is NOT its converse. -/
theorem rejects_bad_value (run : State → State) (s : State) (p : Bool)
    (h : (run s).q ≠ s.q) : ¬ CorrectOracle run s p := by
  intro hc
  exact h hc.1

theorem rejects_bad_phase (run : State → State) (s : State) (p : Bool)
    (h : (run s).phase ≠ Bool.xor s.phase p) :
    ¬ CorrectOracle run s p := by
  intro hc
  exact h hc.2.2

end GVQCC.DQIRefinement316
#print axioms GVQCC.DQIRefinement316.sparse_unique70
#print axioms GVQCC.DQIRefinement316.phaseTarget_congr
#print axioms GVQCC.DQIRefinement316.hmr_exact
#print axioms GVQCC.DQIRefinement316.hmr_necessary
#print axioms GVQCC.DQIRefinement316.oracle_compose
#print axioms GVQCC.DQIRefinement316.rejects_bad_value
#print axioms GVQCC.DQIRefinement316.rejects_bad_phase
