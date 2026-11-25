import Std.Tactic
namespace GVQCC.V58
def bit (a : Bool) : Int := if a then 1 else 0
def par (a b c : Bool) : Bool := Bool.xor (Bool.xor a b) c
def maj (a b c : Bool) : Bool := Bool.xor (Bool.xor (a && b) (a && c)) (b && c)
theorem factor_count (m a b c : Bool) :
    bit (m && a) + bit (m && b) + bit (m && c) =
      bit (m && par a b c) + 2 * bit (m && maj a b c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide
theorem factor_weight (m a b c : Bool) (w : Int) :
    w * (bit (m && a) + bit (m && b) + bit (m && c)) =
      w * (bit (m && par a b c) + 2 * bit (m && maj a b c)) := by
  rw [factor_count]
theorem signed_toggle (r f : Bool) :
    bit (Bool.xor r f) - bit r = bit f * (1 - 2 * bit r) := by
  cases r <;> cases f <;> decide
theorem borrow_toggle (z f r : Bool) :
    bit (Bool.xor z (f && r)) - bit z = (1-2*bit z)*bit f*bit r := by
  cases z <;> cases f <;> cases r <;> decide
theorem interval_delete (z a lo hi : Int) (p : Bool)
    (h₀ : lo ≤ z - a ∧ z - a ≤ hi)
    (h₁ : lo ≤ z + a ∧ z + a ≤ hi) :
    lo ≤ z - (if p then -a else a) ∧ z - (if p then -a else a) ≤ hi := by
  cases p <;> simp_all <;> omega
theorem carry_free_on_disjoint (a b : Bool) (h : (a && b) = false) :
    bit a + bit b = bit (Bool.xor a b) := by
  cases a <;> cases b <;> simp_all [bit]
end GVQCC.V58
