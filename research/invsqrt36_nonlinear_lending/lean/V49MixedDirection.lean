import Std.Tactic
namespace GVQCC.V49
def X := Bool.xor
theorem mixed_direction (P : Bool → Bool → Bool)
    (h : ∀ b, P true b = !(P false (!b)))
    (a b : Bool) (hz : P a b = false) :
    a = P false (X a b) := by
  cases a <;> cases b <;> simp_all [X, Bool.xor]
theorem shear_inverse (a b : Bool) : X a (X a b) = b := by
  cases a <;> cases b <;> decide
theorem shared_factor (a b c d : Bool) :
    X (a && b && c) (a && b && d) = (a && b && X c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem quadratic_transport (a b h k : Bool) :
    (X a h && X b k) = X (X (a && b) (a && k)) (X (h && b) (h && k)) := by
  cases a <;> cases b <;> cases h <;> cases k <;> decide
theorem debt_transport (m p h : Bool) :
    X (m && p) (m && X p h) = (m && h) := by
  cases m <;> cases p <;> cases h <;> decide
theorem ghost_pair (m a b : Bool) :
    X (m && (a && b)) (m && a && b) = false := by
  cases m <;> cases a <;> cases b <;> decide
def bit (a : Bool) : Nat := if a then 1 else 0
theorem quarter_cancel (a b p : Bool)
    (ha : (a && !b) = p) (hb : (b && !a) = false) :
    (3*bit a + bit b) % 4 = (3*bit p) % 4 := by
  cases a <;> cases b <;> cases p <;> simp_all [bit]
theorem parity_character (b : Bool) (w : Int) :
    2*w*(if b then 1 else 0) = w - w*(if b then -1 else 1) := by
  cases b <;> simp <;> omega
theorem receipts : 745-38=707 ∧ 181-52=129 ∧ 91-88=3 := by decide
end GVQCC.V49
