import Std.Tactic
namespace GVQCC.V60
def bit (b : Bool) : Int := if b then 1 else 0
def borrow (a y b : Bool) : Bool :=
  (!a && y) || (!a && b) || (y && b)
theorem borrow_digit (a y b : Bool) :
    bit a - bit y - bit b =
      bit (Bool.xor (Bool.xor a y) b) - 2 * bit (borrow a y b) := by
  cases a <;> cases y <;> cases b <;> decide
theorem exclusive (a b : Bool) (h : (a && b) = false) :
    bit a + bit b = bit (Bool.xor a b) := by
  cases a <;> cases b <;> decide
theorem rounded_absorption (p m : Int) :
    (2*p + m + 8) / 16 = (p + m/2 + 4) / 8 := by omega
theorem rounded_increment (p : Int) :
    (p+4)/8 = p/8 + (p%8)/4 := by omega
theorem guard_borrow (a : Bool) : borrow a false false = false := by
  cases a <;> decide
theorem shared_pivot (p a b : Bool) :
    Bool.xor (p && a) (p && b) = (p && Bool.xor a b) := by
  cases p <;> cases a <;> cases b <;> decide
end GVQCC.V60
