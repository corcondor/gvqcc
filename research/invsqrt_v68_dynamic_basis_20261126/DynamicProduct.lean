import Init
namespace DynamicProduct
theorem transport (f a b : Bool) :
    Bool.xor (f && a) (f && Bool.xor a b) = (f && b) := by
  cases f <;> cases a <;> cases b <;> decide
theorem quadratic_exchange (a b c : Bool) :
    Bool.xor (a && b) (a && c) = (a && Bool.xor b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem abel_three (a b c u v w : Bool) :
    Bool.xor (Bool.xor (a && u) (b && v)) (c && w) =
      Bool.xor (Bool.xor ((Bool.xor (Bool.xor a b) c) && w)
        (a && Bool.xor u v)) ((Bool.xor a b) && Bool.xor v w) := by
  cases a <;> cases b <;> cases c <;> cases u <;> cases v <;> cases w <;> decide
def move (x y g : Bool) : Bool × Bool :=
  let y1 := Bool.xor (Bool.xor y x) g
  let x1 := Bool.xor x y1
  let y2 := Bool.xor (Bool.xor y1 g) x1
  (x1, y2)
theorem masked_move (x y a : Bool) :
    move (Bool.xor x a) y (Bool.xor x y) = (x, Bool.xor y a) := by
  cases x <;> cases y <;> cases a <;> decide
end DynamicProduct
