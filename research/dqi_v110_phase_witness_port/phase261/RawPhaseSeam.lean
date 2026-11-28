import Lean

namespace GVQCC.RawPhaseSeam

-- a = public point times public weight. The mask map is the adjoint of
-- multiplication by a⁻¹. No inversion of a quantum coefficient is implied.
theorem weighted_phase {F : Type} (mul : F → F → F) (dot : F → F → Bool)
    (pull : F → F → F) (a ai e m v : F)
    (value : v = mul a e)
    (leftInv : ∀ x, mul ai (mul a x) = x)
    (adjoint : ∀ x y, dot (pull ai x) y = dot x (mul ai y)) :
    dot (pull ai m) v = dot m e := by
  rw [adjoint, value, leftInv]

-- The quotient of weighted numerator and derivative is invariant under
-- scaling both by the same nonzero field word. Embedding in a ring without
-- a proof of scale cancellation would not justify this step.
theorem projective_equation {F : Type} (mul : F → F → F)
    (s d n v : F)
    (assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (scaleInjective : ∀ a b, mul s a = mul s b → a = b) :
    mul (mul s d) v = mul s n ↔ mul d v = n := by
  rw [assoc]
  constructor
  · exact scaleInjective _ _
  · intro h
    rw [h]

-- Measuring the dirty product leaves a phase debt; the classical outcome
-- selects the same phase polynomial a second time. This is a local lemma,
-- not a circuit-wide HMR or weighted-mask proof.
theorem repay_product_phase (outcome p : Bool) :
    Bool.xor (outcome && p) (outcome && p) = false := by
  cases outcome <;> cases p <;> decide

#print axioms weighted_phase
#print axioms projective_equation
#print axioms repay_product_phase
end GVQCC.RawPhaseSeam
