import Std.Tactic
namespace GVQCC.ChemistryReview
def dot5 (m v : Nat) : Bool :=
  (List.range 5).foldl (fun r i => Bool.xor r (m.testBit i && v.testBit i)) false
def rankWitness (columns : List Nat) : Bool :=
  (List.range 31).all (fun i => columns.any (dot5 (i+1)))
theorem bank4_no_nonzero_kernel : rankWitness [1,22,26,16,21] = true := by decide
theorem bank6_no_nonzero_kernel : rankWitness [22,14,25,11,21] = true := by decide
theorem split_syndrome (u v s : Bool) :
  Bool.xor (Bool.xor u s) (Bool.xor v s) = Bool.xor u v := by
  cases u <;> cases v <;> cases s <;> decide
theorem transport (a b da db : Bool) :
  Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
    Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
end GVQCC.ChemistryReview
