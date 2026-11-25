import Std.Tactic
namespace GVQCC.V52
def bit (b : Bool) : Int := if b then 1 else 0
def chi (b : Bool) : Int := 1 - 2 * bit b
theorem dirty_input_phase (f r : Bool) (w : Int) :
    w * (bit (Bool.xor r f) - bit r) = w * bit f * chi r := by
  cases f <;> cases r <;> simp [bit, chi, Bool.xor] <;> omega
theorem prefix_one (p b : Bool) (w : Int) :
    2 * (w * bit (p && b)) = w * bit p - w * bit p * chi b := by
  cases p <;> cases b <;> simp [bit, chi] <;> omega
theorem prefix_zero (p b : Bool) (w : Int) :
    2 * (w * bit (p && !b)) = w * bit p + w * bit p * chi b := by
  cases p <;> cases b <;> simp [bit, chi] <;> omega
theorem restore_borrowed (r f : Bool) : Bool.xor (Bool.xor r f) f = r := by
  cases r <;> cases f <;> decide
theorem direct_input_width : 2^21 < (3133452 : Nat) ∧ 3133452 ≤ 2^22 := by decide
end GVQCC.V52
