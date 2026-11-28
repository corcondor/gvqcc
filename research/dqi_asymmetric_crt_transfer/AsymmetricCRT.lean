import Std
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace GVQCC.AsymmetricCRT

def xx (a b : Nat) : Nat := Nat.xor a b
def xt (a : Nat) : Nat := if a.testBit 3 then xx (2*a) 19 else 2*a
def xt2 (a : Nat) : Nat := xt (xt a)

def independent (a b c d : Nat) : Bool :=
  (a != 0) && !([0,a].contains b) &&
  !([0,a,b,xx a b].contains c) &&
  !([0,a,b,c,xx a b,xx a c,xx b c,xx (xx a b) c].contains d)

def dep3 (a b c : Nat) : Bool :=
  (a == 0) || (b == 0) || (c == 0) ||
  (a == b) || (a == c) || (b == c) || (xx (xx a b) c == 0)
def le2 (a b c d : Nat) : Bool :=
  dep3 a b c && dep3 a b d && dep3 a c d && dep3 b c d

-- Rank-seven code must be the [7,3,4] simplex code. The four
-- terms seen by the first output can be made coordinate projectors.
-- After multiplying the remaining matrices by U on the left, all
-- three residual matrices must have rank <= 2. Field polynomial x^4+x+1.
def obstruction (a b c d : Nat) : Bool :=
  let a0 := xt a
  let a1 := xx (xt b) b
  let a2 := xt c
  let a3 := xx (xt d) d
  let b0 := xt2 a
  let b1 := xt2 b
  let b2 := xx (xt2 c) c
  let b3 := xx (xt2 d) d
  !(independent a b c d && le2 a0 a1 a2 a3 &&
    le2 b0 b1 b2 b3 && le2 (xx a0 b0) (xx a1 b1) (xx a2 b2) (xx a3 b3))
def allCols (a : Nat) : Bool :=
  (List.range 16).all fun b =>
    (List.range 16).all fun c =>
      (List.range 16).all fun d => obstruction a b c d

theorem no_rank7_basis_0 : allCols 0 = true := by decide
#print axioms no_rank7_basis_0
theorem no_rank7_basis_1 : allCols 1 = true := by decide
#print axioms no_rank7_basis_1
theorem no_rank7_basis_2 : allCols 2 = true := by decide
#print axioms no_rank7_basis_2
theorem no_rank7_basis_3 : allCols 3 = true := by decide
#print axioms no_rank7_basis_3
theorem no_rank7_basis_4 : allCols 4 = true := by decide
#print axioms no_rank7_basis_4
theorem no_rank7_basis_5 : allCols 5 = true := by decide
#print axioms no_rank7_basis_5
theorem no_rank7_basis_6 : allCols 6 = true := by decide
#print axioms no_rank7_basis_6
theorem no_rank7_basis_7 : allCols 7 = true := by decide
#print axioms no_rank7_basis_7
theorem no_rank7_basis_8 : allCols 8 = true := by decide
#print axioms no_rank7_basis_8
theorem no_rank7_basis_9 : allCols 9 = true := by decide
#print axioms no_rank7_basis_9
theorem no_rank7_basis_10 : allCols 10 = true := by decide
#print axioms no_rank7_basis_10
theorem no_rank7_basis_11 : allCols 11 = true := by decide
#print axioms no_rank7_basis_11
theorem no_rank7_basis_12 : allCols 12 = true := by decide
#print axioms no_rank7_basis_12
theorem no_rank7_basis_13 : allCols 13 = true := by decide
#print axioms no_rank7_basis_13
theorem no_rank7_basis_14 : allCols 14 = true := by decide
#print axioms no_rank7_basis_14
theorem no_rank7_basis_15 : allCols 15 = true := by decide
#print axioms no_rank7_basis_15

-- Count the seven possible nonzero coefficient labels of a 3D output.
def comps : Nat → Nat → List (List Nat)
  | 0,n => if n == 0 then [[]] else []
  | k+1,n => (List.range (n+1)).flatMap fun a =>
      (comps k (n-a)).map (fun xs => a :: xs)

def parity3 (x : Nat) : Bool :=
  Bool.xor (x.testBit 0) (Bool.xor (x.testBit 1) (x.testBit 2))
def weight (ns : List Nat) (m : Nat) : Nat :=
  (List.range 7).foldl (fun s i =>
    s + if parity3 ((i+1) &&& m) then ns[i]?.getD 0 else 0) 0
def codeValid (ns : List Nat) : Bool :=
  (List.range 7).all fun i => 4 <= weight ns (i+1)
theorem simplex_labels :
    (comps 7 7).filter codeValid = [[1,1,1,1,1,1,1]] := by decide
#print axioms simplex_labels

-- Independent full count-pattern certificate for 17 degree-one GF(16) places.
-- a=number of output dimension 0, remaining counts b,c,d,e.
def patternGood (a b c d e : Nat) : Bool :=
  let dims := List.replicate a 0 ++ List.replicate b 1 ++ List.replicate c 2 ++
      List.replicate d 3 ++ List.replicate e 4
  !(24 <= (dims.take 12).sum && 4*b+6*c+8*d+9*e < 99)

def allPatterns (a : Nat) : Bool :=
  (comps 4 (17-a)).all fun xs =>
    match xs with
    | [b,c,d,e] => patternGood a b c d e
    | _ => false
theorem cost_pattern_0 : allPatterns 0 = true := by decide
#print axioms cost_pattern_0
theorem cost_pattern_1 : allPatterns 1 = true := by decide
#print axioms cost_pattern_1
theorem cost_pattern_2 : allPatterns 2 = true := by decide
#print axioms cost_pattern_2
theorem cost_pattern_3 : allPatterns 3 = true := by decide
#print axioms cost_pattern_3
theorem cost_pattern_4 : allPatterns 4 = true := by decide
#print axioms cost_pattern_4
theorem cost_pattern_5 : allPatterns 5 = true := by decide
#print axioms cost_pattern_5
theorem cost_pattern_6 : allPatterns 6 = true := by decide
#print axioms cost_pattern_6
theorem cost_pattern_7 : allPatterns 7 = true := by decide
#print axioms cost_pattern_7
theorem cost_pattern_8 : allPatterns 8 = true := by decide
#print axioms cost_pattern_8
theorem cost_pattern_9 : allPatterns 9 = true := by decide
#print axioms cost_pattern_9
theorem cost_pattern_10 : allPatterns 10 = true := by decide
#print axioms cost_pattern_10
theorem cost_pattern_11 : allPatterns 11 = true := by decide
#print axioms cost_pattern_11
theorem cost_pattern_12 : allPatterns 12 = true := by decide
#print axioms cost_pattern_12
theorem cost_pattern_13 : allPatterns 13 = true := by decide
#print axioms cost_pattern_13
theorem cost_pattern_14 : allPatterns 14 = true := by decide
#print axioms cost_pattern_14
theorem cost_pattern_15 : allPatterns 15 = true := by decide
#print axioms cost_pattern_15
theorem cost_pattern_16 : allPatterns 16 = true := by decide
#print axioms cost_pattern_16
theorem cost_pattern_17 : allPatterns 17 = true := by decide
#print axioms cost_pattern_17

theorem affine_product (a b c d : Bool) :
    (Bool.xor a c && Bool.xor b d) =
      Bool.xor (Bool.xor (a && b) (a && d)) (Bool.xor (c && b) (c && d)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
#print axioms affine_product
theorem dirty_update (t a b : Bool) :
    Bool.xor (Bool.xor t (a && b)) (a && b) = t := by
  cases t <;> cases a <;> cases b <;> decide
#print axioms dirty_update
end GVQCC.AsymmetricCRT
