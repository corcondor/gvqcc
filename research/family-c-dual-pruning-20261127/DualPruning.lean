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
end GVQCC.PhaseDual
