import Std.Tactic
set_option autoImplicit false

namespace Gvqcc.NumeratorErase

-- HMR debt and the output-mask pullbacks of the retained products.
-- The caller must establish that its old numerator slice really is lhs + rhs.
theorem conditionalPhaseRepayment (dot : BitVec 12 → BitVec 12 → Bool)
    (old a b mask : BitVec 12)
    (same : old = a ^^^ b)
    (linear : dot mask (a ^^^ b) = Bool.xor (dot mask a) (dot mask b)) :
    Bool.xor (Bool.xor (dot mask old) (dot mask a)) (dot mask b) = false := by
  rw [same, linear]
  cases dot mask a <;> cases dot mask b <;> decide

-- The same check with a faulty old numerator should leave exactly its
-- projection on the HMR record, not erase the evidence of the fault.
theorem residualPhase (dot : BitVec 12 → BitVec 12 → Bool)
    (mask old a b delta : BitVec 12)
    (same : old = (a ^^^ b) ^^^ delta)
    (linear : ∀ x y, dot mask (x ^^^ y) = Bool.xor (dot mask x) (dot mask y)) :
    Bool.xor (Bool.xor (dot mask old) (dot mask a)) (dot mask b) =
      dot mask delta := by
  rw [same, linear (a ^^^ b) delta, linear a b]
  cases dot mask a <;> cases dot mask b <;> cases dot mask delta <;> decide

-- Monic degree-m denominator contributes h to the top coefficient of hB.
theorem removeMonicTop (h : BitVec 12) : h ^^^ h = 0 := BitVec.xor_self

-- Every lower update is the same involutive shear while h and B survive.
theorem monicLowerInvolution (x product : BitVec 12) :
    (x ^^^ product) ^^^ product = x := by
  rw [BitVec.xor_assoc, BitVec.xor_self, BitVec.xor_zero]

#print axioms conditionalPhaseRepayment
#print axioms residualPhase
#print axioms removeMonicTop
#print axioms monicLowerInvolution

end Gvqcc.NumeratorErase
