import Std.Tactic
import Init.Grind.Ring.Basic

set_option autoImplicit false

namespace Gvqcc.EuclideanUnit

-- In characteristic two the congruence r*z = s (mod a) can be written
-- a*k = s + r*z. The merge therefore does not need a stored inverse of a.
theorem euclideanMerge {F : Type} [Lean.Grind.CommRing F]
    (a b r s q p z k : F) (hb : b = a*q+r)
    (hk : a*k = s+r*z) :
    a*(p+q*z+k) = (a*p+s)+b*z := by
  subst b
  grind

-- Pack a known Z word into its own slot, then restore it by the inverse scale.
theorem packedScaleInverse {F : Type} [Lean.Grind.CommRing F]
    (a ai x : F) (h : ai*a = 1) :
    ai*(a*x) = x := by
  grind

-- The triangular shear's dirty target does not need to be cleared.
theorem dirtyShearInverse (x product : BitVec 12) :
    (x ^^^ product) ^^^ product = x := by
  rw [BitVec.xor_assoc, BitVec.xor_self, BitVec.xor_zero]

#print axioms euclideanMerge
#print axioms packedScaleInverse
#print axioms dirtyShearInverse

end Gvqcc.EuclideanUnit
