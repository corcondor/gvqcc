import Std
namespace GVQCC.F4MixedWhole
theorem xor_swap (a b : Bool) : Bool.xor (Bool.xor a b) b = a := by
  cases a <;> cases b <;> decide
theorem product_affine (a b c d : Bool) :
    (Bool.xor a c && Bool.xor b d) =
      Bool.xor (a && b) (Bool.xor (a && d) (Bool.xor (b && c) (c && d))) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem product_shared (a b c u v : Bool) :
    Bool.xor ((a && b) && u) ((a && c) && v) =
      Bool.xor ((a && Bool.xor b c) && u) ((a && c) && Bool.xor u v) := by
  cases a <;> cases b <;> cases c <;> cases u <;> cases v <;> decide
theorem square_add (a b c d : Bool) :
    (Bool.xor (Bool.xor a c) (Bool.xor b d), Bool.xor b d) =
      (Bool.xor (Bool.xor a b) (Bool.xor c d), Bool.xor b d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
#print axioms xor_swap
#print axioms product_affine
#print axioms product_shared
#print axioms square_add
end GVQCC.F4MixedWhole
