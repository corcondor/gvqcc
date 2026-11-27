import Mathlib
import DQIRefinement316

namespace GVQCC.JointOracle316
open scoped BigOperators
open Polynomial

/-- Exact Boolean phase addition, independent of measurement outcomes. -/
theorem step_delta (p q x a b : Bool) :
    Bool.xor (Bool.xor p q) (x && Bool.xor a b) =
      Bool.xor (Bool.xor p (x && a)) (Bool.xor q (x && b)) := by
  cases p <;> cases q <;> cases x <;> cases a <;> cases b <;> decide

theorem fold_delta (l : List ℕ) (e m n : ℕ → Bool) (p q : Bool) :
    l.foldl (fun acc j => Bool.xor acc (e j && Bool.xor (m j) (n j)))
      (Bool.xor p q) =
    Bool.xor
      (l.foldl (fun acc j => Bool.xor acc (e j && m j)) p)
      (l.foldl (fun acc j => Bool.xor acc (e j && n j)) q) := by
  induction l generalizing p q with
  | nil => rfl
  | cons j l ih =>
    simp only [List.foldl_cons]
    rw [step_delta]
    exact ih _ _

theorem phaseTarget_delta (k : ℕ) (e m n : ℕ → Bool) :
    DQIRefinement316.phaseTarget k e (fun j => Bool.xor (m j) (n j)) =
    Bool.xor (DQIRefinement316.phaseTarget k e m)
      (DQIRefinement316.phaseTarget k e n) := by
  exact fold_delta (List.range k) e m n false false

/-- Applying the exact difference character, followed by the rotated
character, restores the original requested phase. -/
theorem repay_rotation (k : ℕ) (e m n : ℕ → Bool) (p : Bool) :
    Bool.xor
      (Bool.xor p (DQIRefinement316.phaseTarget k e
        (fun j => Bool.xor (m j) (n j))))
      (DQIRefinement316.phaseTarget k e n) =
    Bool.xor p (DQIRefinement316.phaseTarget k e m) := by
  rw [phaseTarget_delta]
  cases p <;> cases DQIRefinement316.phaseTarget k e m <;>
    cases DQIRefinement316.phaseTarget k e n <;> decide

/-- Single-pole and all-pole charts are disjoint by their residue tests. -/
theorem shared_tag (a b : Bool) (h : a && b = false) :
    Bool.xor a b = (a || b) := by
  cases a <;> cases b <;> simp_all

theorem shared_tag_erase (t a b : Bool) :
    Bool.xor (Bool.xor (Bool.xor (Bool.xor t a) b) b) a = t := by
  cases t <;> cases a <;> cases b <;> decide

variable {F : Type*} [Field F]

/-- Rational cross-product uniqueness once all finite confluent conditions
have supplied the divisibility and the infinity conditions the strict degree
bound. This is an abstract certificate, not the native interpolation proof. -/
theorem chart_cross_unique (U A T N D : Polynomial F)
    (hU : U ≠ 0)
    (hdvd : U ∣ A*D-N*T)
    (hdegree : (A*D-N*T).natDegree < U.natDegree) :
    A*D = N*T := by
  apply sub_eq_zero.mp
  by_contra hn
  obtain ⟨r, hr⟩ := hdvd
  have hrn : r ≠ 0 := by
    intro hz
    apply hn
    rw [hr, hz, mul_zero]
  rw [hr, Polynomial.natDegree_mul hU hrn] at hdegree
  omega

/-- Leading Laurent coefficients of a degree-34 numerator divided by a
degree-35 denominator. The first is c0 and the second c1. -/
theorem infinity_tail (c0 c1 t35 t34 a33 : F)
    (h0 : c0*t35 = 1) (h1 : c1*t35+c0*t34 = a33) :
    t35 ≠ 0 ∧ c0 = t35⁻¹ ∧ c1 = (a33-c0*t34)/t35 := by
  have ht : t35 ≠ 0 := by
    intro hz
    rw [hz, mul_zero] at h0
    exact zero_ne_one h0
  refine ⟨ht, ?_, ?_⟩
  · field_simp
    exact h0
  · apply (eq_div_iff ht).2
    linear_combination h1

/-- Magnitude from a fixed numerator and its reconstructed locator.
This is the scalar step used by the joint scan, with the nonzero
root, root-free filter and simple-root hypotheses explicit. -/
theorem magnitude_from_inverse (a u x d : F)
    (hu : u ≠ 0) (hx : x ≠ 0) (hd : d ≠ 0) :
    (a/u)*(x*d)⁻¹ = a/(u*x*d) := by
  field_simp

end GVQCC.JointOracle316
#print axioms GVQCC.JointOracle316.step_delta
#print axioms GVQCC.JointOracle316.fold_delta
#print axioms GVQCC.JointOracle316.phaseTarget_delta
#print axioms GVQCC.JointOracle316.repay_rotation
#print axioms GVQCC.JointOracle316.shared_tag
#print axioms GVQCC.JointOracle316.shared_tag_erase
#print axioms GVQCC.JointOracle316.chart_cross_unique
#print axioms GVQCC.JointOracle316.infinity_tail
#print axioms GVQCC.JointOracle316.magnitude_from_inverse
