import Std
namespace GVQCC.ExteriorRank97
theorem shear_control (a b : Bool) :
    (a && Bool.xor a b) = Bool.xor (a && b) a := by
  cases a <;> cases b <;> decide
theorem split_flip (a b c d u v : Bool) :
    Bool.xor ((a && b) && u) ((c && d) && v) =
      Bool.xor ((a && Bool.xor b c) && u)
        (Bool.xor ((c && Bool.xor a d) && u) ((c && d) && Bool.xor u v)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases u <;> cases v <;> decide
theorem shared_factor (a b c u v : Bool) :
    Bool.xor ((a && b) && u) ((a && c) && v) =
      Bool.xor ((a && Bool.xor b c) && u) ((a && c) && Bool.xor u v) := by
  cases a <;> cases b <;> cases c <;> cases u <;> cases v <;> decide
theorem output_echo (a b t : Bool) :
    Bool.xor (Bool.xor t (a && b)) (a && b) = t := by
  cases a <;> cases b <;> cases t <;> decide
#print axioms shear_control
#print axioms split_flip
#print axioms shared_factor
#print axioms output_echo
end GVQCC.ExteriorRank97
