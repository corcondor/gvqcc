import Mathlib

namespace GVQCC.V128
open scoped BigOperators

variable {F : Type*} [CommRing F]
variable {I J R : Type*}

/-- Transposed linear map under the exact bilinear pairing. -/
theorem pairing_transpose (s : Finset I) (t : Finset J)
    (A : I → J → F) (x : J → F) (y : I → F) :
    (∑ i ∈ s, (∑ j ∈ t, A i j * x j) * y i) =
      ∑ j ∈ t, x j * (∑ i ∈ s, A i j * y i) := by
  classical
  calc
    _ = ∑ i ∈ s, ∑ j ∈ t, (A i j * x j) * y i := by
      apply Finset.sum_congr rfl
      intro i _
      rw [Finset.sum_mul]
    _ = ∑ j ∈ t, ∑ i ∈ s, (A i j * x j) * y i := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro j _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro i _
      ring

/-- A certified rank-one tensor decomposition evaluates the desired
bilinear map. The coefficient equalities are separately checked for every
concrete block in the generator; this theorem connects them to all inputs. -/
theorem tensor_contract (s : Finset I) (t : Finset J) (r : Finset R)
    (A : I → J → F) (u : R → I → F) (v : R → J → F)
    (w : R → F) (x : I → F) (y : J → F)
    (h : ∀ i j, A i j = ∑ k ∈ r, u k i * v k j * w k) :
    (∑ i ∈ s, ∑ j ∈ t, x i * y j * A i j) =
      ∑ k ∈ r, (∑ i ∈ s, u k i * x i) * (∑ j ∈ t, v k j * y j) * w k := by
  classical
  calc
    _ = ∑ i ∈ s, ∑ j ∈ t, ∑ k ∈ r, (u k i * x i) * (v k j * y j) * w k := by
      apply Finset.sum_congr rfl
      intro i _
      apply Finset.sum_congr rfl
      intro j _
      rw [h i j, Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro k _
      ring
    _ = ∑ i ∈ s, ∑ k ∈ r, ∑ j ∈ t, (u k i * x i) * (v k j * y j) * w k := by
      apply Finset.sum_congr rfl
      intro i _
      exact Finset.sum_comm
    _ = ∑ k ∈ r, ∑ i ∈ s, ∑ j ∈ t, (u k i * x i) * (v k j * y j) * w k := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro k _
      simp only [Finset.sum_mul, Finset.mul_sum]

/-- Reversal of the low block turns the middle product into a usual
convolution of the low input and dual output. -/
theorem middle_index (a i j : ℕ) (hi : i < a) :
    a+j-i = (a-1-i)+j+1 := by omega

theorem middle_length (a b : ℕ) (ha : 0 < a) (hb : 0 < b) :
    (a-1)+(b-1)+1 = a+b-1 := by omega

theorem frame_difference (x u v : F) : (x+u)+(v-u)=x+v := by ring

theorem dirty_fanout (a b u v : Bool) :
    (Bool.xor u (a && b),
      Bool.xor (Bool.xor v u) (Bool.xor u (a && b))) =
    (Bool.xor u (a && b), Bool.xor v (a && b)) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide

inductive SplitTree where
  | leaf
  | node (l r : SplitTree)
deriving DecidableEq

def SplitTree.size : SplitTree → ℕ
  | .leaf => 1
  | .node l r => l.size + r.size

def SplitTree.cost : SplitTree → ℕ
  | .leaf => 0
  | .node l r => l.cost + r.cost + (l.size + r.size - 1)

def plan35 : SplitTree := (.node (.node (.node (.node (.node .leaf .leaf) (.node .leaf .leaf)) (.node (.node .leaf .leaf) (.node .leaf .leaf))) (.node (.node (.node .leaf .leaf) (.node .leaf .leaf)) (.node (.node .leaf .leaf) (.node .leaf .leaf)))) (.node (.node (.node (.node .leaf .leaf) (.node .leaf .leaf)) (.node (.node .leaf .leaf) (.node .leaf .leaf))) (.node (.node (.node .leaf .leaf) (.node .leaf .leaf)) (.node (.node .leaf (.node .leaf .leaf)) (.node (.node .leaf .leaf) (.node .leaf .leaf))))))

theorem plan35_size : plan35.size = 35 := by decide

theorem plan35_cost : plan35.cost = 147 := by decide

theorem plan35_paid : plan35.cost * 42 = 6174 := by decide

end GVQCC.V128

#print axioms GVQCC.V128.pairing_transpose
#print axioms GVQCC.V128.tensor_contract
#print axioms GVQCC.V128.middle_index
#print axioms GVQCC.V128.middle_length
#print axioms GVQCC.V128.frame_difference
#print axioms GVQCC.V128.dirty_fanout
#print axioms GVQCC.V128.plan35_size
#print axioms GVQCC.V128.plan35_cost
#print axioms GVQCC.V128.plan35_paid
