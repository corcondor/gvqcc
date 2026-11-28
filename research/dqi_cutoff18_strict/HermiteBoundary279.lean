import Mathlib

namespace GVQCC.HermiteBoundary279
open Polynomial

section Field
variable {F : Type*} [Field F]

/-- A first-order jet is u+epsilon*v modulo epsilon^2. -/
def jetMul (a b : F × F) : F × F :=
  (a.1*b.1,a.1*b.2+a.2*b.1)

theorem jet_assoc (a b c : F × F) :
    jetMul (jetMul a b) c = jetMul a (jetMul b c) := by
  apply Prod.ext <;> simp only [jetMul] <;> ring

theorem jet_comm (a b : F × F) :
    jetMul a b = jetMul b a := by
  apply Prod.ext <;> simp only [jetMul] <;> ring

section InverseJet
variable [DecidableEq F]

/-- On nonzero value this is the characteristic-two derivative of inversion.
    At value zero, retain the derivative instead of destroying it. This is
    a reversible completion, not the field inverse of a nonunit jet. -/
noncomputable def invJet (u v : F) : F × F :=
  if u=0 then (0,v) else (u⁻¹,v/u^2)

theorem inv_jet_unit (h : (2:F)=0) (u v : F) (hu : u ≠ 0) :
    jetMul (u,v) (invJet u v) = (1,0) := by
  rw [invJet, ite_eq_right hu]
  apply Prod.ext
  · simp [jetMul, hu]
  · change u*(v/u^2)+v*u⁻¹ = 0
    calc
      _ = (2:F)*(v/u) := by field_simp <;> ring
      _ = 0 := by rw [h, zero_mul]

theorem inv_jet_zero (v : F) : invJet 0 v = (0,v) := by simp [invJet]

theorem inv_jet_involutive (u v : F) :
    invJet (invJet u v).1 (invJet u v).2 = (u,v) := by
  by_cases hu : u=0
  · subst u
    simp [invJet]
  · simp only [invJet, if_neg hu, if_neg (inv_ne_zero hu), inv_inv]
    apply Prod.ext
    · rfl
    · field_simp <;> ring

end InverseJet

/-- The unguarded inverse jet loses its derivative at u=0, unlike the
    zero-safe completion; hence a proof on units alone cannot certify
    the whole physical inverse. -/
theorem clipped_inverse_loses_jet (v : F) :
    ((0 : F), v/(0:F)^2) = ((0:F),0) := by simp

theorem clipped_inverse_noninjective :
    ¬ Function.Injective (fun p : F × F => (p.1⁻¹,p.2/p.1^2)) := by
  intro h
  have he : ((0:F),(0:F)) = (0,1) := by
    apply h
    simp
  exact zero_ne_one (congrArg Prod.snd he)

theorem jet_eval_product (A B : Polynomial F) (x : F) :
    ((A*B).eval x,(derivative (A*B)).eval x) =
      jetMul (A.eval x,(derivative A).eval x) (B.eval x,(derivative B).eval x) := by
  apply Prod.ext
  · simp [jetMul]
  · simp [jetMul, derivative_mul, mul_comm, add_comm]

/-- At a physical root, the padded derivative contains exactly the pad
    evaluation as a multiplicative factor. -/
theorem padded_derivative (D G : Polynomial F) (x : F) (hx : D.eval x=0) :
    (derivative (G*D)).eval x = G.eval x*(derivative D).eval x := by
  simp [derivative_mul, hx, mul_comm]

/-- Includes repeated factors away from the physical root. No squarefree
    hypothesis on G is needed. The pad must not vanish at the root. -/
theorem padded_residue_equiv (D N G : Polynomial F) (x e : F)
    (hx : D.eval x=0) (hg : G.eval x≠0) :
    (G*N).eval x = e*(derivative (G*D)).eval x ↔
      N.eval x = e*(derivative D).eval x := by
  rw [eval_mul, padded_derivative D G x hx]
  have he : e*(G.eval x*(derivative D).eval x) =
      G.eval x*(e*(derivative D).eval x) := by ring
  rw [he]
  constructor
  · exact mul_left_cancel₀ hg
  · intro h
    rw [h]

theorem padded_root_equiv (D G : Polynomial F) (x : F) (hg : G.eval x ≠ 0) :
    (G*D).eval x = 0 ↔ D.eval x=0 := by
  simp [eval_mul,hg]

theorem dual_jet_factor [DecidableEq F] (_h : (2:F)=0) (u v : F) (hu : u≠0) :
    (u^2)*(invJet u v).2 = v := by
  rw [invJet,if_neg hu]
  change u^2*(v/u^2)=v
  field_simp

end Field

section Ring
variable {R : Type*} [CommRing R]

theorem square_sum (h : (2:R)=0) (a b : R) : (a+b)^2=a^2+b^2 := by
  calc
    _ = a^2+b^2+(2:R)*a*b := by ring
    _ = _ := by simp [h]

/-- Full homogeneous half-degree conversion identity.
    No degree-gap, monicity or division assumptions enter this identity. -/
theorem half_degree_identity (h : (2:R)=0)
    (A B U T Z W X P Q : R)
    (hp : P=A*U+B*Z) (hq : Q=A*T+B*W) :
    B^2*((Z+X*T)^2+X*(W+U)^2) =
      P^2+X*Q^2+(A^2+X*B^2)*(U^2+X*T^2) := by
  rw [hp,hq]
  simp only [square_sum h, mul_pow]
  symm
  calc
    _ = B^2*(Z^2+X^2*T^2+X*(W^2+U^2))+
         (2:R)*(A^2*U^2+X*A^2*T^2) := by ring
    _ = _ := by simp [h]

theorem half_degree_derivative (h : (2:R)=0) (A B : Polynomial R) :
    derivative (A^2+X*B^2) = B^2 := by
  simp only [pow_two, derivative_add, derivative_mul, derivative_X, one_mul]
  have hpoly : (2:Polynomial R)=0 := by
    calc
      (2 : Polynomial R) = 1+1 := by ring
      _ = C (1:R)+C (1:R) := by simp
      _ = C (1+1:R) := by rw [map_add]
      _ = 0 := by rw [one_add_one_eq_two,h,map_zero]
  calc
    _ = B*B+(2:Polynomial R)*(A*derivative A+X*B*derivative B) := by ring
    _ = _ := by simp [hpoly]

end Ring

section Phase

/-- If a measured Boolean scratch is a known function of the recovered
    state, repayment cancels the phase for both possible HMR outcomes. -/
theorem repay_any_state {S : Type} (f g : S → Bool) (h : ∀ s,f s=g s)
    (s : S) (m p : Bool) :
    Bool.xor (Bool.xor p (m && f s)) (m && g s) = p := by
  rw [← h s]
  cases m <;> cases p <;> cases f s <;> decide

theorem triple_repay (a b c m p : Bool) :
    Bool.xor (Bool.xor p (m && (a && b && c)))
      (if m then a && b && c else false) = p := by
  cases a <;> cases b <;> cases c <;> cases m <;> cases p <;> decide

/-- The forward/return structure is certified separately from the middle
    phase oracle. A value-roundtrip alone does not certify the phase. -/
theorem oracle_composition {S T : Type} (enc : S → T) (dec : T → S)
    (h : Function.LeftInverse dec enc)
    (middle : T → Bool) (wanted : S → Bool)
    (hp : ∀ s, middle (enc s)=wanted s) (s : S) :
    (dec (enc s),middle (enc s)) = (s,wanted s) := by
  rw [h s,hp s]

theorem zero_residual_phase {I : Type*} (s : Finset I) (m x : I → ZMod 2)
    (hz : ∀ i ∈ s,m i=0) : (∑ i ∈ s,m i*x i)=0 := by
  apply Finset.sum_eq_zero
  intro i hi
  rw [hz i hi,zero_mul]

end Phase

#print axioms jet_assoc
#print axioms jet_comm
#print axioms inv_jet_unit
#print axioms inv_jet_zero
#print axioms inv_jet_involutive
#print axioms clipped_inverse_loses_jet
#print axioms clipped_inverse_noninjective
#print axioms jet_eval_product
#print axioms padded_derivative
#print axioms padded_residue_equiv
#print axioms padded_root_equiv
#print axioms dual_jet_factor
#print axioms square_sum
#print axioms half_degree_identity
#print axioms half_degree_derivative
#print axioms repay_any_state
#print axioms triple_repay
#print axioms oracle_composition
#print axioms zero_residual_phase

end GVQCC.HermiteBoundary279
