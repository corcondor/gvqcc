import Std
namespace GVQCC.FourFieldRank
def times (x y : Bool) := x && y
def low (a b c d : Bool) := Bool.xor (times a c) (times b d)
def high (a b c d : Bool) := Bool.xor (Bool.xor (times a d) (times b c)) (times b d)
theorem gf4_rank3 (a b c d : Bool) :
    low a b c d = Bool.xor (times a c) (times b d) ∧
    high a b c d = Bool.xor (times a c) (times (Bool.xor a b) (Bool.xor c d)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem rank32_budget : 32 * 3 = 96 := by decide
theorem all_sites_budget : 329 * (99 - 96) + 4 * (99 - 96) = 999 := by decide
#print axioms gf4_rank3
#print axioms rank32_budget
#print axioms all_sites_budget
end GVQCC.FourFieldRank
