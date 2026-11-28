import Std.Tactic
set_option autoImplicit false

namespace Gvqcc.WindowTransport

-- A dirty output anchor may be used if its induced contribution is repaid.
-- The result is independent of the incoming anchor and target words.
theorem dirtyOutputShear (a t d : BitVec 12) (scale : BitVec 12 → BitVec 12)
    (hl : scale (a ^^^ d) = scale a ^^^ scale d) :
    (t ^^^ scale a) ^^^ scale (a ^^^ d) = t ^^^ scale d := by
  rw [hl, BitVec.xor_assoc t (scale a) (scale a ^^^ scale d), ← BitVec.xor_assoc (scale a), BitVec.xor_self, BitVec.zero_xor]

-- If a masked high-product has been reversed as degree L+R-2,
-- quotient coefficient j points to product coefficient L+R-2-j.
theorem reverseCoefficient (l r j : Nat) (hl : 0 < l) (hr : 0 < r)
    (hj : j < l + r - 1) :
    l + r - 2 - (l + r - 2 - j) = j := by
  omega

-- The known monic term X^m of B has no contribution to low_m(BQ).
theorem monicOutsideWindow (m j : Nat) (h : j < m) :
    ¬ ∃ i : Nat, m + i = j := by
  omega

-- Multiplication takes place in the quotient by monic B. Its two inputs
-- can carry reciprocal scale factors independently of the representative.
theorem projectiveHalfCoordinate {R : Type} (mul : R → R → R)
    (assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (s si c p : R) (cancel : ∀ x, mul si (mul s x) = x) :
    mul (mul c si) (mul s p) = mul c p := by
  rw [assoc, cancel]

#print axioms dirtyOutputShear
#print axioms reverseCoefficient
#print axioms monicOutsideWindow
#print axioms projectiveHalfCoordinate

end Gvqcc.WindowTransport
