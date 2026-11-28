import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic

/-!
A Farkas-style obstruction to modifying a fixed Boolean phase basis.
Necessary only: a nonzero pairing does NOT imply feasibility.
The binding between a certificate matrix and the physical KMB is separate.
-/
namespace GVQCC.PhaseDual
open scoped BigOperators

private theorem weighted_old_zero {m n : Nat}
    (A : Fin m → Fin n → Int) (weights : Fin m → Nat)
    (θ : Fin n → Int)
    (hcol : ∀ j : Fin n, (∑ i : Fin m, (weights i : Int) * A i j) = 0) :
    (∑ i : Fin m, (weights i : Int) * (∑ j : Fin n, A i j * θ j)) = 0 := by
  calc
    _ = ∑ i : Fin m, ∑ j : Fin n,
          ((weights i : Int) * A i j) * θ j := by
      simp_rw [Finset.mul_sum, mul_assoc]
    _ = ∑ j : Fin n, ∑ i : Fin m,
          ((weights i : Int) * A i j) * θ j := Finset.sum_comm
    _ = ∑ j : Fin n,
          (∑ i : Fin m, (weights i : Int) * A i j) * θ j := by
      simp_rw [Finset.sum_mul]
    _ = 0 := by simp [hcol]

/-- A nonnegative integer dual with negative RHS excludes all angle deltas. -/
theorem no_fixed_basis_solution {m n : Nat}
    (A : Fin m → Fin n → Int) (rhs : Fin m → Int) (w : Fin m → Nat)
    (hcol : ∀ j : Fin n, (∑ i : Fin m, (w i : Int) * A i j) = 0)
    (hneg : (∑ i : Fin m, (w i : Int) * rhs i) < 0) :
    ¬ ∃ θ : Fin n → Int, ∀ i : Fin m,
      (∑ j : Fin n, A i j * θ j) ≤ rhs i := by
  rintro ⟨θ, ht⟩
  have hs :
      (∑ i : Fin m, (w i : Int) * (∑ j : Fin n, A i j * θ j)) ≤
      (∑ i : Fin m, (w i : Int) * rhs i) := by
    apply Finset.sum_le_sum
    intro i _
    exact mul_le_mul_of_nonneg_left (ht i) (by positivity)
  rw [weighted_old_zero A w θ hcol] at hs
  omega

/-- If a newly added control predicate is orthogonal to the same dual,
its angle cannot repair the infeasible set of inequalities. -/
theorem one_new_column_still_impossible {m n : Nat}
    (A : Fin m → Fin n → Int) (B : Fin m → Int)
    (rhs : Fin m → Int) (w : Fin m → Nat)
    (hcol : ∀ j : Fin n, (∑ i : Fin m, (w i : Int) * A i j) = 0)
    (hB : (∑ i : Fin m, (w i : Int) * B i) = 0)
    (hneg : (∑ i : Fin m, (w i : Int) * rhs i) < 0) :
    ¬ ∃ θ : Fin n → Int, ∃ φ : Int, ∀ i : Fin m,
        (∑ j : Fin n, A i j * θ j) + B i * φ ≤ rhs i := by
  rintro ⟨θ, φ, ht⟩
  have hs :
      (∑ i : Fin m, (w i : Int) *
        ((∑ j : Fin n, A i j * θ j) + B i * φ)) ≤
      (∑ i : Fin m, (w i : Int) * rhs i) := by
    apply Finset.sum_le_sum
    intro i _
    exact mul_le_mul_of_nonneg_left (ht i) (by positivity)
  have hnew : (∑ i : Fin m, (w i : Int) * (B i * φ)) = 0 := by
    calc
      _ = (∑ i : Fin m, (w i : Int) * B i) * φ := by
        simp_rw [← mul_assoc, Finset.sum_mul]
      _ = 0 := by rw [hB]; ring
  have hz :
      (∑ i : Fin m, (w i : Int) *
        ((∑ j : Fin n, A i j * θ j) + B i * φ)) = 0 := by
    calc
      _ = (∑ i : Fin m, (w i : Int) * (∑ j : Fin n, A i j * θ j)) +
          (∑ i : Fin m, (w i : Int) * (B i * φ)) := by
        simp_rw [mul_add, Finset.sum_add_distrib]
      _ = 0 := by rw [weighted_old_zero A w θ hcol, hnew]; ring
  rw [hz] at hs
  omega

/-- Any successful extra predicate must pair nontrivially with this dual. -/
theorem successful_new_column_nonorthogonal {m n : Nat}
    (A : Fin m → Fin n → Int) (B : Fin m → Int)
    (rhs : Fin m → Int) (w : Fin m → Nat)
    (hcol : ∀ j : Fin n, (∑ i : Fin m, (w i : Int) * A i j) = 0)
    (hneg : (∑ i : Fin m, (w i : Int) * rhs i) < 0)
    (θ : Fin n → Int) (φ : Int)
    (hfeasible : ∀ i : Fin m,
        (∑ j : Fin n, A i j * θ j) + B i * φ ≤ rhs i) :
    (∑ i : Fin m, (w i : Int) * B i) ≠ 0 := by
  intro hzero
  exact one_new_column_still_impossible A B rhs w hcol hzero hneg
    ⟨θ, φ, hfeasible⟩

#print axioms no_fixed_basis_solution
#print axioms one_new_column_still_impossible
#print axioms successful_new_column_nonorthogonal

/-! Concrete rational dual from the public Family-C upclear (33 rotations,
    32 signed input inequalities). This is a *fixed signed phase sheet*.
    Source KMB SHA256 bc5f4a97d85e9a6d7717f9f5f6f6184349259b2b7baf4ca934d304b69f3cc8ba.
    The finite arithmetic is certified, not the KMB-to-mask extraction. -/
namespace UpclearRefit
private def masks : Fin 32 → Nat :=
  ![6136781692, 3660437628, 7982152759, 5312340743, 694615857,
    1717369712, 2373402416, 6414395249, 3884596273, 657316672,
    6802955077, 4863164224, 4246617940, 4151721792, 6864191312,
    868416833, 1854858241, 6237897793, 1506462789, 2076696657,
    8384922709, 6225840465, 6346032469, 2780496148, 2231304464,
    2164197652, 2357133568, 2352621828, 70909968, 2364940564,
    2364942352, 2226594048]
private def signs : Fin 32 → Int :=
  ![1, -1, 1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1, 1, -1,
    -1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
private def weights : Fin 32 → Nat :=
  ![36024, 36024, 112041, 112041, 105509, 86502, 245470, 150446,
    36024, 75566, 6501, 25088, 50889, 33994, 10172, 1588,
    10454, 20213, 12935, 23400, 40139, 46563, 71140, 20724,
    20862, 24722, 236, 10007, 17733, 11371, 24769, 31369]
private def rhs : Fin 32 → Int :=
  ![610124475, -6224839094, -2594304834, -6127525773,
    -493156349, -4508369292, -7456741298, -2029972920,
    -2581423809, -104499084, 28494684, -3081335937,
    -1622531598, -67611399, -232799629, 312153852,
    -808582273, 236971897, -191815526, 62420839, 137427369,
    -286559264, 447652721, -19907474, 358033099, -32254105,
    381427729, 274179015, 26177235, -92777796, -70737209, 236893344]
private def A (i : Fin 32) (j : Fin 33) : Int :=
  if (masks i).testBit j.val then signs i else 0

theorem kernel_dual_cancellation :
    ∀ j : Fin 33, (∑ i : Fin 32, (weights i : Int) * A i j) = 0 := by decide

theorem kernel_negative_bound :
    (∑ i : Fin 32, (weights i : Int) * rhs i) =
    (-3988521952806357 : Int) := by decide

theorem fixed_sheet_unreachable :
    ¬ ∃ θ : Fin 33 → Int, ∀ i : Fin 32,
        (∑ j : Fin 33, A i j * θ j) ≤ rhs i := by
  apply no_fixed_basis_solution A rhs weights kernel_dual_cancellation
  rw [kernel_negative_bound]
  omega

#print axioms kernel_dual_cancellation
#print axioms kernel_negative_bound
#print axioms fixed_sheet_unreachable
end UpclearRefit

end GVQCC.PhaseDual
