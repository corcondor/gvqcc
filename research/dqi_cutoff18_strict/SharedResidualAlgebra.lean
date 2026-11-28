import Mathlib

namespace GVQCC.SharedResidualAlgebra
open Polynomial
open scoped BigOperators
noncomputable section
variable {F : Type*} [Field F]

section Interpolation
variable [DecidableEq F]

/-- The 71 anchor words determine X times an ordinary interpolant.
    There are 72 coefficients, including the forced zero constant. -/
def weightedPoly (s : Finset F) (mu : F → F) : Polynomial F :=
  X * Lagrange.interpolate s id (fun a => mu a / a)

theorem weighted_zero (s : Finset F) (mu : F → F) :
    (weightedPoly s mu).eval 0 = 0 := by
  simp [weightedPoly]

theorem weighted_at_anchor (s : Finset F) (mu : F → F) (a : F)
    (ha : a ∈ s) (h0 : a ≠ 0) :
    (weightedPoly s mu).eval a = mu a := by
  have hi : Set.InjOn (id : F → F) (↑s : Set F) := fun _ _ _ _ h => h
  have he := Lagrange.eval_interpolate_at_node (fun x : F => mu x / x) hi ha
  simp only [id_eq] at he
  rw [weightedPoly, eval_mul, eval_X, he]
  field_simp

theorem weighted_degree (s : Finset F) (mu : F → F) (_hs : s.Nonempty) :
    (weightedPoly s mu).natDegree ≤ s.card := by
  let q := Lagrange.interpolate s id (fun a : F => mu a / a)
  change (X*q).natDegree ≤ s.card
  by_cases hq : q = 0
  · simp [hq]
  have hi : Set.InjOn (id : F → F) (↑s : Set F) := fun _ _ _ _ h => h
  have hh : q.degree < (s.card : WithBot Nat) :=
    Lagrange.degree_interpolate_lt (fun a : F => mu a / a) hi
  rw [degree_eq_natDegree hq] at hh
  have hn : q.natDegree < s.card := by exact_mod_cast hh
  calc
    (X*q).natDegree ≤ (X : Polynomial F).natDegree + q.natDegree := natDegree_mul_le
    _ ≤ s.card := by rw [natDegree_X]; omega

/-- With 71 distinct nonzero anchors and the additional zero node,
    agreement on these 72 nodes determines every coefficient. -/
theorem weighted_unique (s : Finset F) (p q : Polynomial F)
    (h0 : 0 ∉ s) (hp : p.natDegree ≤ s.card) (hq : q.natDegree ≤ s.card)
    (hz : p.eval 0 = q.eval 0)
    (he : ∀ a ∈ s, p.eval a = q.eval a) : p = q := by
  apply Polynomial.eq_of_natDegree_lt_card_of_eval_eq' p q (insert 0 s)
  · intro a ha
    rcases Finset.mem_insert.mp ha with h | h
    · rw [h]; exact hz
    · exact he a h
  · rw [Finset.card_insert_of_notMem h0]
    omega

theorem weighted_interpolation_unique (s : Finset F) (mu : F → F)
    (p : Polynomial F) (h0 : 0 ∉ s) (hs : s.Nonempty)
    (hp : p.natDegree ≤ s.card) (hz : p.eval 0 = 0)
    (ha : ∀ a ∈ s, p.eval a = mu a) :
    p = weightedPoly s mu := by
  apply weighted_unique s p (weightedPoly s mu) h0 hp (weighted_degree s mu hs)
  · rw [hz, weighted_zero]
  · intro a hm
    have hn : a ≠ 0 := fun h => h0 (h ▸ hm)
    rw [ha a hm, weighted_at_anchor s mu a hm hn]

/-- The full evaluation transform is linear in the supplied anchor data. -/
theorem weighted_add (s : Finset F) (mu nu : F → F) :
    weightedPoly s (fun x => mu x + nu x) =
    weightedPoly s mu + weightedPoly s nu := by
  unfold weightedPoly
  have he : (fun x : F => (mu x + nu x) / x) =
      (fun x : F => mu x / x) + (fun x : F => nu x / x) := by
    funext x
    simp [add_div]
  rw [he, map_add, mul_add]

theorem weighted_scale (s : Finset F) (mu : F → F) (c : F) :
    weightedPoly s (fun x => c * mu x) = C c * weightedPoly s mu := by
  unfold weightedPoly
  rw [Lagrange.interpolate_apply,Lagrange.interpolate_apply]
  have hh : (∑ j ∈ s, C (c*mu j/j)*Lagrange.basis s id j) =
      C c*(∑ j ∈ s, C (mu j/j)*Lagrange.basis s id j) := by
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro j _
    rw [mul_div_assoc, map_mul]
    ring
  rw [hh]
  ring

end Interpolation

/-- Exact row factorization used by prepare_fft.py. The row-coefficient
    certificate is an explicit hypothesis, rather than an assumed theorem
    about the binary KMB. -/
theorem residual_row_factor {I : Type*} (s : Finset I)
    (coef ell mu : I → F) (rho x m : F)
    (hc : ∀ j ∈ s, coef j = rho*x*ell j) :
    rho*m + ∑ j ∈ s, coef j*mu j =
      rho*(m+x*(∑ j ∈ s, ell j*mu j)) := by
  calc
    _ = rho*m + ∑ j ∈ s, (rho*x)*(ell j*mu j) := by
      congr 1
      apply Finset.sum_congr rfl
      intro j hj
      rw [hc j hj]
      ring
    _ = _ := by rw [← Finset.mul_sum, mul_add, mul_assoc]

/-- Transposition of a moment/evaluation pairing; this justifies moving
    a public mask in the moment span into a syndrome-linear phase. -/
theorem moment_transport {I J : Type*} (s : Finset I) (t : Finset J)
    (e : I → F) (a : J → F) (b : I → J → F) :
    (∑ i ∈ s, e i*(∑ j ∈ t, a j*b i j)) =
      ∑ j ∈ t, a j*(∑ i ∈ s, e i*b i j) := by
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem moment_polynomial (s : Finset F) (t : Finset Nat)
    (e : F → F) (a : Nat → F) :
    (∑ x ∈ s, e x*(∑ j ∈ t, a j*x^(j+1))) =
      ∑ j ∈ t, a j*(∑ x ∈ s, e x*x^(j+1)) :=
  moment_transport s t e a (fun x j => x^(j+1))

theorem moment_phase (s : Finset F) (t : Finset Nat)
    (tau : F →+ ZMod 2) (e : F → F) (a : Nat → F) :
    tau (∑ x ∈ s, e x*(∑ j ∈ t, a j*x^(j+1))) =
      tau (∑ j ∈ t, a j*(∑ x ∈ s, e x*x^(j+1))) := by
  rw [moment_polynomial]

/-- The row/basis check proves equality of the *linear map* on arbitrary
    inputs, not just on the checked basis vectors. -/
theorem matrix_ext_on_inputs {I J : Type*} (t : Finset J)
    (M N : I → J → F) (h : ∀ i j, j ∈ t → M i j = N i j) (u : J → F) :
    ∀ i, (∑ j ∈ t, M i j*u j) = ∑ j ∈ t, N i j*u j := by
  intro i
  apply Finset.sum_congr rfl
  intro j hj
  rw [h i j hj]

/-- Characteristic-two subspace polynomial recurrence in the generator:
    S = P / P(beta), Pnext=P^2+P(beta)*P. -/
theorem square_add_two (h : (2:F)=0) (a b : F) : (a+b)^2 = a^2+b^2 := by
  calc
    _ = a^2+b^2+(2:F)*a*b := by ring
    _ = _ := by simp [h]

def subStep (P : Polynomial F) (v : F) := P^2+C v*P

theorem sub_step_eval (P : Polynomial F) (v x : F) :
    (subStep P v).eval x = (P.eval x)^2+v*P.eval x := by
  simp [subStep]

theorem sub_step_additive (h : (2:F)=0) (P : Polynomial F) (v : F)
    (ha : ∀ a b, P.eval (a+b) = P.eval a+P.eval b) (a b : F) :
    (subStep P v).eval (a+b) = (subStep P v).eval a+(subStep P v).eval b := by
  simp only [sub_step_eval, ha, square_add_two h]
  ring

theorem sub_step_zero (P : Polynomial F) (v x : F) (hx : P.eval x = 0) :
    (subStep P v).eval x = 0 := by simp [sub_step_eval, hx]

theorem sub_step_new_root (h : (2:F)=0) (P : Polynomial F) (x : F) :
    (subStep P (P.eval x)).eval x = 0 := by
  rw [sub_step_eval]
  calc
    _ = (2:F)*(P.eval x)^2 := by ring
    _ = 0 := by rw [h, zero_mul]

theorem sub_step_shift (h : (2:F)=0) (P : Polynomial F) (x beta : F)
    (ha : ∀ a b, P.eval (a+b) = P.eval a+P.eval b) :
    (subStep P (P.eval beta)).eval (x+beta) =
      (subStep P (P.eval beta)).eval x := by
  rw [sub_step_additive h P _ ha, sub_step_new_root h, add_zero]

theorem normalized_shift (P : Polynomial F) (x beta : F)
    (hb : P.eval beta ≠ 0)
    (ha : ∀ a b, P.eval (a+b) = P.eval a+P.eval b) :
    P.eval (x+beta)/P.eval beta = P.eval x/P.eval beta+1 := by
  rw [ha, add_div, div_self hb]

theorem basis_split_eval (A B S : Polynomial F) (x : F) :
    (A+S*B).eval x = A.eval x+S.eval x*B.eval x := by simp

theorem fft_sibling_eval (A B S : Polynomial F) (x y : F)
    (hs : S.eval y = S.eval x+1) :
    (A+S*B).eval y = A.eval y+(S.eval x+1)*B.eval y := by
  rw [basis_split_eval,hs]

#print axioms weighted_zero
#print axioms weighted_at_anchor
#print axioms weighted_degree
#print axioms weighted_unique
#print axioms weighted_interpolation_unique
#print axioms residual_row_factor
#print axioms weighted_add
#print axioms weighted_scale
#print axioms moment_transport
#print axioms moment_polynomial
#print axioms moment_phase
#print axioms matrix_ext_on_inputs
#print axioms square_add_two
#print axioms sub_step_eval
#print axioms sub_step_additive
#print axioms sub_step_zero
#print axioms sub_step_new_root
#print axioms sub_step_shift
#print axioms normalized_shift
#print axioms basis_split_eval
#print axioms fft_sibling_eval

end
end GVQCC.SharedResidualAlgebra
