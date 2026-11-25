import Std.Tactic
namespace GVQCC.V56
def bit (b : Bool) : Nat := if b then 1 else 0
def maj (a b c : Bool) : Bool := Bool.xor (Bool.xor (a && b) (a && c)) (b && c)
def par (a b c : Bool) : Bool := Bool.xor (Bool.xor a b) c
theorem triple_count (a b c : Bool) :
    bit a + bit b + bit c = bit (par a b c) + 2 * bit (maj a b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem seven_count (a b c d e f g : Bool) :
    bit a + bit b + bit c + bit d + bit e + bit f + bit g =
      bit (par (par a b c) (par d e f) g) +
      2 * bit (par (maj a b c) (maj d e f) (maj (par a b c) (par d e f) g)) +
      4 * bit (maj (maj a b c) (maj d e f) (maj (par a b c) (par d e f) g)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> cases f <;> cases g <;> decide
theorem onehot_product (f g u v x y : Bool) (h : (f && g) = false) :
    Bool.xor (f && u && v) (g && x && y) =
      (Bool.xor (f && u) (g && x) && Bool.xor (f && v) (g && y)) := by
  cases f <;> cases g <;> cases u <;> cases v <;> cases x <;> cases y <;> (first | decide | contradiction)
theorem phase_debt (r a b c : Bool) :
    (r && Bool.xor a (b && c)) = Bool.xor (r && a) (r && b && c) := by
  cases r <;> cases a <;> cases b <;> cases c <;> decide
theorem delta_frame (a b : Bool) : Bool.xor a (Bool.xor a b) = b := by
  cases a <;> cases b <;> decide
end GVQCC.V56
