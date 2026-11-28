import Std
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace Rank97CosetAudit

-- Symmetric rank-one matrices in 4D, packed upper triangular coordinates.
def dict : List Nat := [1,4,7,32,41,52,63,512,577,644,711,800,873,948,1023]
def piv : List Nat := [1,4,7,32,41,52,512,577,644,800]
def ker : List Nat := [127,1927,6553,10922,19252]
def combine (xs : List Nat) (m : Nat) : Nat :=
  (List.range xs.length).foldl
    (fun v i => if m.testBit i then Nat.xor v (xs[i]?.getD 0) else v) 0
def kernelMasks : List Nat := (List.range 32).map (combine ker)
def coset (m : Nat) : List Nat := kernelMasks.map (Nat.xor m)
def weight (m : Nat) : Nat :=
  (List.range 15).foldl (fun z i => if m.testBit i then z+1 else z) 0
def extend8 (xs ys : List Nat) : List Nat :=
  xs.flatMap (fun x => (ys.map (fun y => x ||| y)).filter (fun v => weight v ≤ 8))

theorem rank10_certificate :
    (List.range 1024).all (fun m => m == 0 || combine piv m != 0) = true := by decide
theorem kernel_independence :
    (List.range 32).all (fun m => m == 0 || combine ker m != 0) = true := by decide
theorem kernel_valid :
    kernelMasks.all (fun m => combine dict m == 0) = true := by decide
theorem four_output_cosets :
    (coset 2849).all (fun m => combine dict m == 976) = true ∧
    (coset 2354).all (fun m => combine dict m == 376) = true ∧
    (coset 2584).all (fun m => combine dict m == 429) = true ∧
    (coset 932).all (fun m => combine dict m == 758) = true := by decide
theorem no_eight_support :
    extend8 (extend8 (extend8 (extend8 [0] (coset 2849)) (coset 2354)) (coset 2584)) (coset 932) = [] := by decide

def terms : List (Nat × Nat) :=
    [(1,1),(2,2),(3,3),(4,4),(8,8),(12,12),(5,13),(10,6),(15,11)]
def slice (k : Nat) : Nat :=
    terms.foldl (fun z (a,c) => if c.testBit k then Nat.xor z (dict[a-1]?.getD 0) else z) 0
theorem nine_certificate :
    terms.length = 9 ∧ (List.range 4).map slice = [976,376,429,758] := by decide
theorem group_bound_arithmetic : 11 * 9 = 99 ∧ 333 * (99 - 97) = 666 := by decide

-- Boolean plane equivalence modulo affine repayment.
theorem mixed_control_debt (a b : Bool) :
    ((a && b) != (a && (a != b))) = a := by cases a <;> cases b <;> decide
theorem pooled_output (a b c : Bool) :
    (a && (b != c)) = ((a && b) != (a && c)) := by cases a <;> cases b <;> cases c <;> decide

#print axioms rank10_certificate
#print axioms kernel_independence
#print axioms kernel_valid
#print axioms four_output_cosets
#print axioms no_eight_support
#print axioms nine_certificate
#print axioms group_bound_arithmetic
#print axioms mixed_control_debt
#print axioms pooled_output
end Rank97CosetAudit
