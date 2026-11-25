import Std.Tactic
namespace GVQCC.V55

def x (a b : Bool) : Bool := Bool.xor a b
def bit (a : Bool) : Nat := if a then 1 else 0
def maj (a b c : Bool) : Bool := x a (x a b && x a c)
theorem tensor_merge (u v p q : Bool) :
    x (u && v && p) (u && v && q) = (u && v && x p q) := by
  cases u <;> cases v <;> cases p <;> cases q <;> decide

theorem shared_fanout (u v a b : Bool) :
    let a' := x a (u && v)
    (a', x (x b a) a') = (x a (u && v), x b (u && v)) := by
  cases u <;> cases v <;> cases a <;> cases b <;> decide

theorem majority_correct (a b c : Bool) :
    maj a b c = x (x (a && b) (a && c)) (b && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem angle_carry (a b c : Bool) :
    bit a + bit b + bit c =
      bit (x (x a b) c) + 2 * bit (maj a b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem measured_majority (a b c m : Bool) :
    x (m && maj a b c)
      (x (m && a) (m && x a b && x a c)) = false := by
  cases a <;> cases b <;> cases c <;> cases m <;> decide

theorem integer_phase_complement (a : Int) (f : Bool) :
    a * (bit f : Int) = a - a * (bit (!f) : Int) := by
  cases f <;> simp [bit]

theorem abel_step (p c m d z : Bool) :
    x (p && c) (x (m && x c d) z) =
      x (x p m && c) (x (m && d) z) := by
  cases p <;> cases c <;> cases m <;> cases d <;> cases z <;> decide

theorem native_counts :
    17687 - 15405 = 2282 ∧ 15405 + 3498 = 18903 ∧
    5390 - 1041 = 4349 ∧ 21820 - 18903 = 2917 := by decide
end GVQCC.V55
