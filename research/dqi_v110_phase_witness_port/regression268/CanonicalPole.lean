import Std.Tactic
import Init.Grind.Ring.Basic

set_option autoImplicit false

namespace Gvqcc.CanonicalPole

/-- The guard is an invariant of the first output word block. No persistent
    flag is needed in the unscaled canonical chart semantics. -/
theorem guardResidue {R S : Type} [Mul R] [Zero S] [DecidableEq S]
    (rem : R → S) (q d : R) (hq : rem (q*d) = 0) :
    rem (if rem d = 0 then q*d else d) = rem d := by
  by_cases h : rem d = 0
  · rw [ite_eq_left h, hq, h]
  · rw [ite_eq_right h]

/-- Ordinarily the second output is the exact quotient. This identity is
    independent of the numerical value of the ordinary head h. -/
theorem regularInverse {R : Type} [Lean.Grind.CommRing R]
    (n d q h v : R) (rel : q*v = n+h*d) : q*v-h*d = n := by
  grind

/-- The forward pole map contributes one chart factor. Dropping it exactly
    at the reverse step avoids accumulated degree growth. -/
theorem poleInverse {R : Type} [Mul R] (divide : R → R) (q n d : R)
    (cancel : divide (q*d) = d) :
    ((q*d,n).2,divide (q*d,n).1) = (n,d) := by
  simp [cancel]

#print axioms guardResidue
#print axioms regularInverse
#print axioms poleInverse

end Gvqcc.CanonicalPole
