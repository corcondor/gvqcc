import Mathlib

namespace GVQCC.AdaptivePivot316
open Polynomial
open scoped BigOperators

/-- A degree-bounded nonzero numerator cannot vanish at all available roots.
The root set is in the quadratic extension, including both conjugates. -/
theorem pivot_available {F : Type*} [Field F] (P : Polynomial F) (s : Finset F)
    (r : ℕ) (hP : P ≠ 0) (hdeg : P.natDegree < r) (hroots : r ≤ s.card) :
    ∃ x ∈ s, P.eval x ≠ 0 := by
  classical
  by_contra! hall
  exact hP (Polynomial.eq_zero_of_natDegree_lt_card_of_eval_eq_zero' P s hall
    (lt_of_lt_of_le hdeg hroots))

/-- Each distinct quadratic node contributes two distinct conjugate roots,
whereas no node accounts for more than two remaining slots. -/
theorem slot_budget {I : Type*} (s : Finset I) (m : I → ℕ)
    (hm : ∀ i ∈ s, m i ≤ 2) :
    (∑ i ∈ s, m i) ≤ 2*s.card := by
  calc
    (∑ i ∈ s, m i) ≤ ∑ i ∈ s, (2 : ℕ) := Finset.sum_le_sum hm
    _ = 2*s.card := by simp [Nat.mul_comm]

/-- Weighted degree bound for the actual inverse-head polynomial step.
Q=0 is handled explicitly; natDegree 0 must not be interpreted as a degree. -/
theorem regular_budget {F : Type*} [Field F]
    (N D H G Q : Polynomial F) (r : ℕ)
    (hn : N.natDegree < r) (hd : D.natDegree ≤ r)
    (hh : H.natDegree ≤ 1) (hg : G.natDegree = 2) (hg0 : G ≠ 0)
    (he : G*Q = D+H*N) :
    (Q = 0 ∨ Q.natDegree < r-1) ∧ N.natDegree ≤ r-1 := by
  constructor
  · by_cases hz : Q = 0
    · exact Or.inl hz
    · right
      have hm : (H*N).natDegree ≤ r :=
        le_trans (Polynomial.natDegree_mul_le) (by omega)
      have ha : (D+H*N).natDegree ≤ r :=
        le_trans (Polynomial.natDegree_add_le _ _) (max_le hd hm)
      rw [← he, Polynomial.natDegree_mul hg0 hz, hg] at ha
      omega
  · omega

/-- The homogeneous transform is nonsingular at every different node. -/
theorem projective_nonzero {F : Type*} [Field F] (n d h g : F)
    (hg : g ≠ 0) (hnd : n ≠ 0 ∨ d ≠ 0) :
    d+h*n ≠ 0 ∨ g*n ≠ 0 := by
  by_cases hn : n=0
  · left
    simpa [hn] using hnd.resolve_left (fun hne => hne hn)
  · right
    exact mul_ne_zero hg hn

/-- Common scale g does not alter the projective representation. -/
theorem projective_step {R : Type*} [CommRing R] (n d h g q : R)
    (he : g*q=d+h*n) :
    (d+h*n, g*n) = (g*q,g*n) := by rw [he]

/-- At the selected quadratic root, g=0 and g'=1. The next numerator
is its derivative quotient, without an inverse of the zero g. -/
theorem selected_derivative {R : Type*} [CommRing R]
    (dp h np hp n q g gp qp : R)
    (hg : g = 0) (hgp : gp = 1)
    (he : dp+hp*n+h*np=gp*q+g*qp) :
    q=dp+h*np+hp*n := by
  rw [hg,hgp,one_mul,zero_mul,add_zero] at he
  linear_combination -he

/-- Coprimality survives the exact regular division. -/
theorem bezout_step {R : Type*} [CommRing R]
    (n d h g q : R) (he : g*q=d+h*n)
    (hb : ∃ a b : R, a*n+b*d=1) :
    ∃ a b : R, a*q+b*n=1 := by
  obtain ⟨a,b,hab⟩ := hb
  refine ⟨b*g,a-b*h,?_⟩
  calc
    (b*g)*q+(a-b*h)*n = b*(g*q)+(a-b*h)*n := by ring
    _ = a*n+b*d := by rw [he]; ring
    _ = 1 := hab

/-- When the numerator is identically zero the residual denominator is
a unit; no further artificial head or singular division is necessary. -/
theorem terminal_denominator {R : Type*} [CommRing R]
    (d : R) (h : ∃ a b : R, a*0+b*d=1) :
    ∃ b : R, b*d=1 := by
  obtain ⟨a,b,hab⟩ := h
  exact ⟨b,by simpa using hab⟩

end GVQCC.AdaptivePivot316
#print axioms GVQCC.AdaptivePivot316.pivot_available
#print axioms GVQCC.AdaptivePivot316.slot_budget
#print axioms GVQCC.AdaptivePivot316.regular_budget
#print axioms GVQCC.AdaptivePivot316.projective_nonzero
#print axioms GVQCC.AdaptivePivot316.projective_step
#print axioms GVQCC.AdaptivePivot316.selected_derivative
#print axioms GVQCC.AdaptivePivot316.bezout_step
#print axioms GVQCC.AdaptivePivot316.terminal_denominator
