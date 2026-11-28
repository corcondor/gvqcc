import Mathlib

namespace GVQCC.ExactTransposedLagrange
open Polynomial
open scoped BigOperators
noncomputable section
variable {F : Type*} [Field F]

/-- Actual Lagrange coefficient used by #283, not an assumed certificate. -/
def lagCoeff {k : Nat} (x : Fin k → F) (t : Fin k) (a : Nat) : F :=
  (Lagrange.basis Finset.univ x t).coeff a

theorem monomial_interpolation {k : Nat} (x : Fin k → F)
    (hx : Function.Injective x) (d : Nat) (hd : d < k) :
    Lagrange.interpolate Finset.univ x (fun t => x t ^ d) =
      (X : Polynomial F)^d := by
  have hi : Set.InjOn x (↑(Finset.univ : Finset (Fin k)) : Set (Fin k)) :=
    hx.injOn
  have hdeg : ((X : Polynomial F)^d).degree <
      ((Finset.univ : Finset (Fin k)).card : WithBot Nat) := by
    rw [degree_X_pow, Finset.card_univ, Fintype.card_fin]
    exact_mod_cast hd
  simpa only [eval_pow, eval_X] using
    (Lagrange.eq_interpolate (s := Finset.univ) (v := x)
      (f := (X : Polynomial F)^d) hi hdeg).symm

/-- Discharges the certificate hypothesis of #283 middle_entry. -/
theorem lagrange_certificate {k : Nat} (x : Fin k → F)
    (hx : Function.Injective x) (a d : Nat) (hd : d < k) :
    (∑ t, lagCoeff x t a * x t ^ d) = if a = d then 1 else 0 := by
  have he := congrArg (fun p : Polynomial F => p.coeff a)
    (monomial_interpolation x hx d hd)
  rw [Lagrange.interpolate_apply, finsetSum_coeff, coeff_X_pow] at he
  simp only [coeff_C_mul] at he
  simpa only [lagCoeff, mul_comm] using he

/-- Rank-(l+r-1) tensor, with actual Lagrange coefficients. The reversed
    RHS power implements the middle coefficient extraction. -/
theorem exact_middle_entry {l r : Nat} (x : Fin (l+r-1) → F)
    (hx : Function.Injective x) (a : Fin (l+r-1)) (j : Fin r) (i : Fin l) :
    (∑ t, lagCoeff x t a.val * x t ^ (r-1-j.val) * x t ^ i.val) =
      if a.val+j.val = r-1+i.val then 1 else 0 := by
  have hj := j.isLt
  have hi := i.isLt
  have hd : r-1-j.val+i.val < l+r-1 := by omega
  have he : (a.val = r-1-j.val+i.val) ↔ (a.val+j.val = r-1+i.val) := by omega
  simp_rw [mul_assoc, ← pow_add]
  rw [lagrange_certificate x hx _ _ hd]
  simp only [he]

/-- Real coefficient functional shared by both right-hand sides. -/
def encode {k t : Nat} (u : Fin t → Fin k → F) :
    (Fin k → F) →ₗ[F] (Fin t → F) where
  toFun b s := ∑ a, b a * u s a
  map_add' b c := by
    funext s
    simp only [Pi.add_apply, add_mul, Finset.sum_add_distrib]
  map_smul' c b := by
    funext s
    simp only [Pi.smul_apply, smul_eq_mul, RingHom.id_apply, mul_assoc, Finset.mul_sum]

/-- Arbitrary-input contraction: a certificate for the tensor entries
    suffices to prove the entire bilinear update, even on dirty targets. -/
theorem contraction {k l r t : Nat}
    (u : Fin t → Fin k → F) (v : Fin t → Fin r → F)
    (w : Fin t → Fin l → F) (b : Fin k → F) (p : Fin r → F)
    (i : Fin l) (z : F) (M : Fin k → Fin r → Fin l → F)
    (hc : ∀ a j i, (∑ s, u s a * v s j * w s i) = M a j i) :
    z+(∑ s, encode u b s*(∑ j, p j*v s j)*w s i) =
      z+∑ a, ∑ j, (b a*p j)*M a j i := by
  congr 1
  change (∑ s, (∑ a, b a*u s a)*(∑ j, p j*v s j)*w s i) = _
  calc
    _ = ∑ s, ∑ a, ∑ j, (b a*p j)*(u s a*v s j*w s i) := by
      apply Finset.sum_congr rfl
      intro s _
      simp only [Finset.sum_mul, Finset.mul_sum]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro j _
      ring
    _ = ∑ a, ∑ j, ∑ s, (b a*p j)*(u s a*v s j*w s i) := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro a _
      rw [Finset.sum_comm]
    _ = _ := by
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro j _
      rw [← Finset.mul_sum, hc]

theorem exact_middle_update {l r : Nat} (x : Fin (l+r-1) → F)
    (hx : Function.Injective x) (b : Fin (l+r-1) → F) (p : Fin r → F)
    (i : Fin l) (z : F) :
    z+(∑ s, encode (fun t a => lagCoeff x t a.val) b s *
        (∑ j : Fin r, p j*x s ^ (r-1-j.val))*x s ^ i.val) =
      z+∑ a : Fin (l+r-1), ∑ j : Fin r,
          (b a*p j)*(if a.val+j.val = r-1+i.val then 1 else 0) := by
  exact contraction _ _ _ _ _ _ _ _ (exact_middle_entry x hx)

/-- Every coefficient of the transposed Toeplitz tensor occurs in a
    matrix entry. This supplies the left flattening rank obstruction. -/
theorem coefficient_visible {l r : Nat} (hl : 0 < l) (hr : 0 < r)
    (a : Fin (l+r-1)) :
    ∃ (i : Fin l) (j : Fin r), a.val+j.val = r-1+i.val := by
  have ha := a.isLt
  refine ⟨⟨a.val-(r-1), by omega⟩, ⟨r-1-a.val, by omega⟩, ?_⟩
  change a.val+(r-1-a.val) = r-1+(a.val-(r-1))
  omega

theorem flattening_recover {k l r t : Nat}
    (u : Fin t → Fin k → F) (v : Fin t → Fin r → F)
    (w : Fin t → Fin l → F) (b : Fin k → F)
    (j : Fin r) (i : Fin l) (M : Fin k → Fin r → Fin l → F)
    (hc : ∀ a j i, (∑ s, u s a*v s j*w s i)=M a j i) :
    (∑ s, encode u b s*v s j*w s i) = ∑ a, b a*M a j i := by
  change (∑ s, (∑ a, b a*u s a)*v s j*w s i) = _
  simp_rw [Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro a _
  simp_rw [mul_assoc]
  rw [← Finset.mul_sum]
  have h := hc a j i
  simp_rw [mul_assoc] at h
  rw [h]

/-- Optimality in the bilinear word-rank model, not a lower bound on
    general Boolean CCX count. Every separated rank-one decomposition
    of the full middle tensor needs at least l+r-1 terms. -/
theorem middle_rank_lower_bound {l r t : Nat} (hl : 0 < l) (hr : 0 < r)
    (u : Fin t → Fin (l+r-1) → F) (v : Fin t → Fin r → F)
    (w : Fin t → Fin l → F)
    (hc : ∀ a j i, (∑ s, u s a*v s j*w s i) =
      if a.val+j.val = r-1+i.val then 1 else 0) :
    l+r-1 ≤ t := by
  have hi : Function.Injective (encode u) := by
    intro b c he
    funext a
    obtain ⟨i,j,hij⟩ := coefficient_visible hl hr a
    have recover (p : Fin (l+r-1) → F) :
        (∑ s, encode u p s*v s j*w s i)=p a := by
      rw [flattening_recover u v w p j i _ hc]
      have hiff (a' : Fin (l+r-1)) :
          (a'.val+j.val=r-1+i.val) ↔ a'=a := by
        constructor
        · intro h
          apply Fin.ext
          omega
        · intro h
          rw [h]
          exact hij
      simp [hiff]
    rw [← recover b, ← recover c, he]
  have hdim := LinearMap.finrank_le_finrank_of_injective hi
  simpa only [Module.finrank_pi, Fintype.card_fin] using hdim

#print axioms monomial_interpolation
#print axioms lagrange_certificate
#print axioms exact_middle_entry
#print axioms contraction
#print axioms exact_middle_update
#print axioms coefficient_visible
#print axioms flattening_recover
#print axioms middle_rank_lower_bound
end
end GVQCC.ExactTransposedLagrange
