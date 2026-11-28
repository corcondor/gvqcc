import Std
namespace GVQCC.MixedQuadratic97

theorem mixed_linear_repay (a b : Bool) :
    xor (a && xor a b) a = (a && b) := by
  cases a <;> cases b <;> decide

theorem wedge_flip (a b c d : Bool) :
    xor (a && b) (c && d) =
      xor (a && xor b d) (xor a c && d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem common_flip (p a b u v : Bool) :
    xor (p && a && u) (p && b && v) =
      xor (p && xor a b && u) (p && b && xor v u) := by
  cases p <;> cases a <;> cases b <;> cases u <;> cases v <;> decide

theorem mixed_dirty_target (a b t : Bool) :
    xor (xor t (a && xor a b)) a = xor t (a && b) := by
  cases a <;> cases b <;> cases t <;> decide

def terms : List (Nat × Nat × Nat) :=
  [(10,14,4),(7,15,7),(8,12,6),(9,8,3),(1,4,2),(5,13,6),(3,6,7),(6,11,5)]

def slice (k : Nat) : Nat :=
  terms.foldl (fun z (a,b,c) =>
    if c.testBit k then
      Nat.xor z ((List.range 4).foldl (fun v j =>
        if b.testBit j then v + a * 2^(4*j) else v) 0)
    else z) 0

theorem partial_GF16_observer : terms.length = 8 ∧
    (List.range 3).map slice = [33825,14402,25476] := by decide

-- Full local jet multiplication over GF4: three 3-product GF4 operations.
def jet : List (Nat × Nat × Nat) :=
  [(1,1,15),(4,4,12),(5,5,12),(2,2,5),(8,8,4),(10,10,4),(3,3,10),(12,12,8),(15,15,8)]

def jetSlice (k : Nat) : Nat :=
  jet.foldl (fun z (a,b,c) =>
    if c.testBit k then
      Nat.xor z ((List.range 4).foldl (fun v j =>
        if b.testBit j then v + a * 2^(4*j) else v) 0)
    else z) 0

theorem jet_length : jet.length = 9 := by decide

theorem split_product (a b c : Bool) :
    xor (a && xor b c) (a && c) = (a && b) := by
  cases a <;> cases b <;> cases c <;> decide

#print axioms mixed_linear_repay
#print axioms wedge_flip
#print axioms common_flip
#print axioms mixed_dirty_target
#print axioms partial_GF16_observer
#print axioms jet_length
#print axioms split_product
end GVQCC.MixedQuadratic97
