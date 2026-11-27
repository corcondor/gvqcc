import Init
namespace GVQCC.CarryPhase
def bx (a b : Bool) := Bool.xor a b
def maj (a b c : Bool) := bx c (bx a c && bx b c)
def sum (a b c : Bool) := bx (bx a b) c

-- Complementing the updated sum recovers the original carry in inverse addition.
theorem inverse_carry (a b c : Bool) :
    maj a (!(sum a b c)) c = maj a b c := by
  cases a <;> cases b <;> cases c <;> decide

-- Clean hybrid carry from b xor c and a xor c; the sum is written after erasure.
theorem hybrid_carry (a b c : Bool) :
    bx (bx c ((bx a c) && (bx b c))) c = ((bx a c) && (bx b c)) := by
  cases a <;> cases b <;> cases c <;> decide
theorem hybrid_sum (a b c : Bool) :
    bx a (bx b c) = sum a b c := by
  cases a <;> cases b <;> cases c <;> decide

-- HMR phase correction for polynomial sum terms, with arbitrary outcome.
theorem phase_xor (m a b : Bool) :
    (m && bx a b) = bx (m && a) (m && b) := by
  cases m <;> cases a <;> cases b <;> decide
theorem phase_triple (m a b c : Bool) :
    (m && (a && b && c)) = ((m && a && b) && c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide
theorem phase_quad (m a b c d : Bool) :
    (m && (a && b && c && d)) = ((m && a && b) && (m && c && d)) := by
  cases m <;> cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem phase_erase_product (a b m m2 : Bool) :
    bx (m2 && (m && a && b)) (m && m2 && a && b) = false := by
  cases a <;> cases b <;> cases m <;> cases m2 <;> decide

-- Two-AND row23 relation in a phase-oriented factored form.
theorem phase23 (m v2 v3 v4 v5 p : Bool) :
    let g := (bx (bx v2 v3) v4) && bx v5 p
    let h := m && g
    (m && bx (bx v3 g) (bx v4 g && bx v3 p)) =
      bx (bx (m && v3) h) (m && (bx v4 h && bx v3 p)) := by
  cases m <;> cases v2 <;> cases v3 <;> cases v4 <;> cases v5 <;> cases p <;> decide

-- No charge or global phase error after conditional phase repayment on a promised digit.
theorem phase_cancel (s f m : Bool) (hf : s = f) :
    bx (m && s) (m && f) = false := by
  subst s
  cases m <;> cases f <;> decide
end GVQCC.CarryPhase
#print axioms GVQCC.CarryPhase.inverse_carry
#print axioms GVQCC.CarryPhase.hybrid_carry
#print axioms GVQCC.CarryPhase.hybrid_sum
#print axioms GVQCC.CarryPhase.phase_xor
#print axioms GVQCC.CarryPhase.phase_triple
#print axioms GVQCC.CarryPhase.phase_quad
#print axioms GVQCC.CarryPhase.phase_erase_product
#print axioms GVQCC.CarryPhase.phase23
#print axioms GVQCC.CarryPhase.phase_cancel
