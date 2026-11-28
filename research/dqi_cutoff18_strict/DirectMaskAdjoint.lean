import Mathlib

namespace GVQCC.DirectMaskAdjoint
open scoped BigOperators
open Polynomial

section Algebra
variable {F : Type*} [Field F]

theorem root_remainder (P G R Q : Polynomial F) (x : F)
    (h : G = P * Q + R) (hz : P.eval x = 0) :
    G.eval x = R.eval x := by
  rw [h, eval_add, eval_mul, hz, zero_mul, zero_add]

/-- Push a classical coefficient covector through the joint interpolation
    tensor before performing any quantum product. -/
theorem joint_adjoint {I J : Type*} [Fintype I] [Fintype J]
    (L : I → J → F) (w : I → F) (a b c d : J → F) :
    (∑ i, w i * (∑ j, L i j * (a j*b j+c j*d j))) =
      ∑ j, (∑ i, w i * L i j) * (a j*b j+c j*d j) := by
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  rw [Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem joint_interpolation {k : Nat} (x : Fin k → F)
    (hx : Function.Injective x) (a b c d : Polynomial F)
    (h : (a*b+c*d).degree < (k : WithBot Nat)) :
    Lagrange.interpolate Finset.univ x (fun t =>
      a.eval (x t)*b.eval (x t)+c.eval (x t)*d.eval (x t)) =
      a*b+c*d := by
  have hi : Set.InjOn x (↑(Finset.univ : Finset (Fin k)) : Set (Fin k)) :=
    hx.injOn
  have hd : (a*b+c*d).degree <
      ((Finset.univ : Finset (Fin k)).card : WithBot Nat) := by
    simpa only [Finset.card_univ, Fintype.card_fin] using h
  simpa only [eval_add, eval_mul] using
    (Lagrange.eq_interpolate (s := Finset.univ) (v := x)
      (f := a*b+c*d) hi hd).symm

/-- The syndromes are indexed from exponent one, not zero. -/
theorem moment_pairing {I J : Type*} [Fintype I] [Fintype J]
    (e x : I → F) (a : J → F) (k : J → Nat) :
    (∑ i, e i*x i*(∑ j, a j*(x i)^k j)) =
      ∑ j, a j*(∑ i, e i*(x i)^(k j+1)) := by
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  rw [pow_succ]
  ring

/-- Any trace-dual mask on the support, represented by a residue polynomial,
    can be paired with the raw moments without reconstructing magnitudes. -/
theorem mask_pairing {I J : Type*} [Fintype I] [Fintype J]
    (e x m : I → F) (a : J → F) (k : J → Nat)
    (h : ∀ i, m i = x i*(∑ j, a j*(x i)^k j)) :
    (∑ i, e i*m i) = ∑ j, a j*(∑ i, e i*(x i)^(k j+1)) := by
  calc
    _ = ∑ i, e i*x i*(∑ j, a j*(x i)^k j) := by
      apply Finset.sum_congr rfl
      intro i _
      rw [h i]
      ring
    _ = _ := moment_pairing e x a k

theorem phase_pairing {I J : Type*} [Fintype I] [Fintype J]
    (trace : F →+ ZMod 2) (e x m : I → F) (a : J → F) (k : J → Nat)
    (h : ∀ i, m i = x i*(∑ j, a j*(x i)^k j)) :
    trace (∑ i, e i*m i) =
      trace (∑ j, a j*(∑ i, e i*(x i)^(k j+1))) := by
  rw [mask_pairing e x m a k h]

theorem trace_product_sum (tr : F →+ ZMod 2) (m a b c d : F) :
    tr (m*(a*b+c*d)) = tr (m*a*b)+tr (m*c*d) := by
  rw [mul_add, map_add]
  congr 1 <;> ring

/-- Quotient first-row normalization: the consumed prefix relation survives
    projective scaling without reconstructing the second row. -/
theorem normalize_row (D N S T : Polynomial F) (p : F) (n : Nat)
    (h : D*S+N = X^n*T) :
    (C p*D)*S+C p*N = X^n*(C p*T) := by
  calc
    _ = C p*(D*S+N) := by ring
    _ = _ := by rw [h]; ring

theorem eval_move (a old new : F) : (a+old)+(new-old)=a+new := by ring
theorem eval_restore (a v : F) : a+v-v=a := by ring

end Algebra

section BooleanPhase

theorem z_pull (a b t : Bool) :
    Bool.xor (Bool.xor t (a && b)) t = (a && b) := by
  cases a <;> cases b <;> cases t <;> decide

theorem masked_z_pull (a b t m : Bool) :
    Bool.xor ((Bool.xor t (a && b)) && m) (t && m) =
      (a && b && m) := by
  cases a <;> cases b <;> cases t <;> cases m <;> decide

theorem hmr_debt_transport (a b t m r : Bool) :
    Bool.xor ((Bool.xor t (a && b)) && m)
       ((Bool.xor t (a && b)) && r) =
    Bool.xor (Bool.xor (t && m) (t && r)) (a && b && Bool.xor m r) := by
  cases a <;> cases b <;> cases t <;> cases m <;> cases r <;> decide

theorem phase_only_echo (a b t m : Bool) :
    Bool.xor (Bool.xor t (a && b)) (a && b) = t ∧
    Bool.xor ((Bool.xor t (a && b)) && m) (t && m) =
      (a && b && m) := by
  cases a <;> cases b <;> cases t <;> cases m <;> decide

end BooleanPhase
end GVQCC.DirectMaskAdjoint

#print axioms GVQCC.DirectMaskAdjoint.root_remainder
#print axioms GVQCC.DirectMaskAdjoint.joint_adjoint
#print axioms GVQCC.DirectMaskAdjoint.joint_interpolation
#print axioms GVQCC.DirectMaskAdjoint.moment_pairing
#print axioms GVQCC.DirectMaskAdjoint.mask_pairing
#print axioms GVQCC.DirectMaskAdjoint.phase_pairing
#print axioms GVQCC.DirectMaskAdjoint.trace_product_sum
#print axioms GVQCC.DirectMaskAdjoint.normalize_row
#print axioms GVQCC.DirectMaskAdjoint.eval_move
#print axioms GVQCC.DirectMaskAdjoint.eval_restore
#print axioms GVQCC.DirectMaskAdjoint.z_pull
#print axioms GVQCC.DirectMaskAdjoint.masked_z_pull
#print axioms GVQCC.DirectMaskAdjoint.hmr_debt_transport
#print axioms GVQCC.DirectMaskAdjoint.phase_only_echo
