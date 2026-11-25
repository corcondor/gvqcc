import Init
namespace GlobalDualTensor
theorem pair_transport (a b c d : Bool) :
    Bool.xor (Bool.xor ((Bool.xor a d) && (Bool.xor c b)) (a && c)) (b && d) =
      Bool.xor (a && b) (c && d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem delta_chain (a b : Bool) : Bool.xor a (Bool.xor a b) = b := by
  cases a <;> cases b <;> decide
end GlobalDualTensor
