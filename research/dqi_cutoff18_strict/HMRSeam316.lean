import Mathlib

namespace GVQCC.HMRSeam316

/-- A padded rational pair with a common nonconstant factor cannot
    satisfy the coprime Bézout boundary assumed by the old converter. -/
theorem common_factor_obstruction {F : Type*} [Field F]
    (G d n u v : Polynomial F) (hg : 0 < G.natDegree) :
    u*(G*d)+v*(G*n) ≠ 1 := by
  intro h
  have he : G*(u*d+v*n)=1 := by
    calc
      _ = u*(G*d)+v*(G*n) := by ring
      _ = 1 := h
  have hG : G ≠ 0 := by
    intro h0
    rw [h0, zero_mul] at he
    exact zero_ne_one he
  have hR : u*d+v*n ≠ 0 := by
    intro h0
    rw [h0, mul_zero] at he
    exact zero_ne_one he
  have hh := Polynomial.natDegree_mul hG hR
  rw [he, Polynomial.natDegree_one] at hh
  omega

/-- Reset can be an injective chart change only when the discarded
    coordinate is a function of the retained state. -/
theorem erase_injective_on_graph {A B : Type*} (f : A → B)
    (x y : A × B) (hx : x.2=f x.1) (hy : y.2=f y.1)
    (h : x.1=y.1) : x=y := by
  exact Prod.ext h (by rw [hx,hy,h])

theorem erase_collision {A B : Type*} (a : A) (b c : B) (h : b≠c) :
    (a,b) ≠ (a,c) := by
  intro h'
  exact h (congrArg Prod.snd h')

/-- The original diagonal measurement-bit lifetime has two phases.
    A correct HMR debt is exactly their XOR. -/
theorem debt_boundary (h p0 p1 : Bool) :
    (∀ m : Bool, Bool.xor (m && h) (if m then p1 else p0) = p0) ↔
    h = Bool.xor p0 p1 := by
  cases h <;> cases p0 <;> cases p1 <;> decide

/-- Replace every phase-only consumer of the private result by its m=0
    value, and pay the debt immediately using the exact live witness. -/
theorem immediate_repayment (h p0 m : Bool) :
    Bool.xor (m && h) (Bool.xor (m && h) p0)=p0 := by
  cases h <;> cases p0 <;> cases m <;> decide

theorem agree_on_correct_domain (h p0 p1 m : Bool)
    (hc : h=Bool.xor p0 p1) :
    Bool.xor (m && h) (if m then p1 else p0) = p0 :=
  (debt_boundary h p0 p1).2 hc m

/-- Classical control distributes across the complete affine frame. -/
theorem affine_repayment (m c a b : ZMod 2) :
    m*(c+a+b) = m*c+m*a+m*b := by ring

/-- Each term of a quadratic witness is a Clifford phase conditioned on
    a private classical measurement result. -/
theorem quadratic_repayment (m c d a b : ZMod 2) :
    m*((c+a)*(d+b)) = m*(c*d)+m*(c*b)+m*(a*d)+m*(a*b) := by ring

theorem square_collapse (m a : Bool) :
    (m && a && a) = (m && a) := by
  cases m <;> cases a <;> decide

end GVQCC.HMRSeam316

#print axioms GVQCC.HMRSeam316.common_factor_obstruction
#print axioms GVQCC.HMRSeam316.erase_injective_on_graph
#print axioms GVQCC.HMRSeam316.erase_collision
#print axioms GVQCC.HMRSeam316.debt_boundary
#print axioms GVQCC.HMRSeam316.immediate_repayment
#print axioms GVQCC.HMRSeam316.agree_on_correct_domain
#print axioms GVQCC.HMRSeam316.affine_repayment
#print axioms GVQCC.HMRSeam316.quadratic_repayment
#print axioms GVQCC.HMRSeam316.square_collapse
