import Std.Tactic

set_option autoImplicit false

namespace Gvqcc.EuclideanUnit

-- T_G extends its truncated action by one top row d. T_F fixes that
-- coordinate. Expanding linearity, removing the row is one XOR after fusion.
theorem retractBoundary {n : Nat}
    (outer : BitVec n → BitVec n) (v t d : BitVec n)
    (completed : v = t ^^^ d)
    (linear : outer (t ^^^ d) = outer t ^^^ outer d)
    (fix : outer d = d) :
    outer v ^^^ d = outer t := by
  rw [completed, linear, fix, BitVec.xor_assoc, BitVec.xor_self, BitVec.xor_zero]

-- The correction depends only on the retained high words; it can be
-- undone before returning to the old frame.
theorem boundaryInverse {n : Nat} (a d : BitVec n) : (a ^^^ d) ^^^ d = a := by
  rw [BitVec.xor_assoc, BitVec.xor_self, BitVec.xor_zero]

#print axioms retractBoundary
#print axioms boundaryInverse

end Gvqcc.EuclideanUnit

