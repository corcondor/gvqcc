import Std
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace Rank99MultiGroup

def parity : List Bool → Bool
  | [] => false
  | x :: xs => Bool.xor x (parity xs)

theorem common_factor (a : Bool) (xs : List Bool) :
    parity (xs.map (fun x => a && x)) = (a && parity xs) := by
  induction xs with
  | nil => cases a <;> decide
  | cons x xs ih =>
    change Bool.xor (a && x) (parity (xs.map (fun y => a && y))) =
      (a && Bool.xor x (parity xs))
    rw [ih]
    generalize parity xs = p
    cases a <;> cases x <;> cases p <;> decide

theorem rank_two (a b c u v w : Bool) :
    Bool.xor (Bool.xor (a && b && u) (a && c && v)) (a && Bool.xor b c && w) =
    Bool.xor (a && b && Bool.xor u w) (a && c && Bool.xor v w) := by
  cases a <;> cases b <;> cases c <;> cases u <;> cases v <;> cases w <;> decide

theorem observer_debt (a b m n : Bool) :
    Bool.xor (a && b && m) (a && b && n) = (a && b && Bool.xor m n) := by
  cases a <;> cases b <;> cases m <;> cases n <;> decide

def entry (ts : List (Nat × Nat)) (i j : Nat) : Bool :=
  parity (ts.map (fun (a,b) => a.testBit i && b.testBit j))

-- Actual 3-term -> 2-term group emitted by the 10000-step audit.
theorem observed_group_exact :
    (List.range 24).all (fun i =>
      (List.range 24).all (fun j =>
        entry [(13,12799641),(9,13),(13,12799640)] i j ==
        entry [(13,1),(9,13)] i j)) = true := by decide

-- Symmetric rank-one matrix dictionary for four binary coordinates.
def dict4 : List Nat := [1,32,51,1024,1285,1632,1911,32768,36873,41120,45243,52224,56589,61152,65535]
def combine (xs : List Nat) (m : Nat) : Nat :=
  (List.range xs.length).foldl
    (fun v i => if m.testBit i then Nat.xor v (xs[i]?.getD 0) else v) 0

def pivot4 : List Nat := [1,32,51,1024,1285,1632,32768,36873,41120,52224]
def kernel4 : List Nat := [127,1927,6553,10922,19252]
def kernelMasks : List Nat := (List.range 32).map (combine kernel4)
def coset (m : Nat) : List Nat := kernelMasks.map (Nat.xor m)
def wt (m : Nat) : Nat :=
  (List.range 15).foldl (fun z i => if m.testBit i then z+1 else z) 0
def extend8 (xs ys : List Nat) : List Nat :=
  xs.flatMap (fun x => (ys.map (fun y => x ||| y)).filter (fun v => wt v ≤ 8))

theorem pivot_independence :
  (List.range 1024).all (fun m => m == 0 || combine pivot4 m != 0) = true := by decide
theorem kernel_independence :
  (List.range 32).all (fun m => m == 0 || combine kernel4 m != 0) = true := by decide
theorem kernel_valid : kernelMasks.all (fun m => combine dict4 m == 0) = true := by decide
theorem four_output_cosets :
  (coset 3).all (fun m => combine dict4 m == 33) = true ∧
  (coset 5).all (fun m => combine dict4 m == 50) = true ∧
  (coset 667).all (fun m => combine dict4 m == 8580) = true ∧
  (coset 809).all (fun m => combine dict4 m == 13000) = true := by decide

-- Rank 10 of the symmetric dictionary (pivot independence and the 10-dimensional
-- symmetric matrix space) makes the five-dimensional kernel exhaustive.
-- The finite union-of-support certificate below excludes a shared support of size <=8.
theorem no_eight_support :
    extend8 (extend8 (extend8 (extend8 [0] (coset 3)) (coset 5)) (coset 667)) (coset 809) = [] := by decide

def dual4 : List (Nat × Nat × Nat) :=
  [(1,1,15),(2,2,5),(3,3,2),(4,4,12),(5,5,4),(6,6,8),(8,8,4),(9,9,8),(10,10,12)]
def slice (ts : List (Nat × Nat × Nat)) (k : Nat) : Nat :=
  ts.foldl (fun z (a,b,c) => if c.testBit k then Nat.xor z
    ((List.range 4).foldl (fun u i =>
      (List.range 4).foldl (fun v j =>
        if a.testBit i && b.testBit j then v + 2^(4*i+j) else v) u) 0) else z) 0
theorem nine_support_certificate :
  dual4.length = 9 ∧ (List.range 4).map (slice dual4) = [33,50,8580,13000] := by decide

-- Canonical ANF polynomials, each monomial encoded by its set of variables.
abbrev Poly := List Nat
def toggle (p : Nat) : Poly → Poly
  | [] => [p]
  | q :: qs => if p = q then qs else if p < q then p :: q :: qs else q :: toggle p qs
def addPoly (p q : Poly) : Poly := p.foldl (fun a x => toggle x a) q
def mulPoly (p q : Poly) : Poly :=
  p.foldl (fun a x => q.foldl (fun b y => toggle (x ||| y) b) a) []
abbrev Gate := Nat × Nat × Nat × Nat
def readWire (s : List Poly) (i : Nat) : Poly := s[i]?.getD []
def step (s : List Poly) (g : Gate) : List Poly :=
  let (op,a,b,t) := g
  let x := readWire s a
  let y := readWire s b
  if op = 33 then s.set b (addPoly x y)
  else if op = 34 then (s.set a y).set b x
  else s.set t (addPoly (mulPoly x y) (readWire s t))
def run (gs : List Gate) : List Poly :=
  gs.foldl step ((List.range 14).map (fun i => [2^i]))
def rawOld : List Gate := [(49,0,1,10),(33,1,0,0),(34,1,2,0),(33,10,1,0),(34,2,3,0),(33,10,2,0),(34,3,7,0),(34,7,8,0),(34,8,12,0),(34,12,13,0),(34,13,5,0),(33,0,5,0),(33,4,5,0),(33,5,4,0),(33,11,4,0),(33,4,11,0),(33,6,11,0),(34,6,9,0),(33,11,9,0),(33,10,9,0),(33,9,10,0),(49,1,2,10),(33,9,1,0),(33,9,2,0),(33,10,9,0),(33,10,1,0),(33,9,10,0),(33,9,1,0),(34,11,6,0),(34,4,6,0),(34,5,6,0),(34,13,6,0),(34,12,6,0),(34,8,6,0),(34,7,6,0),(34,3,6,0),(34,2,6,0),(33,1,10,0),(33,1,9,0),(34,1,6,0),(49,2,3,10),(33,10,9,0),(33,10,6,0),(33,10,2,0),(33,10,1,0),(33,9,6,0),(33,9,4,0),(33,9,5,0),(33,9,13,0),(33,9,3,0),(33,9,2,0),(33,6,10,0),(33,6,8,0),(33,6,3,0),(33,6,2,0),(33,6,1,0),(33,6,0,0),(33,11,10,0),(33,11,1,0),(33,11,0,0),(33,4,9,0),(33,4,6,0),(33,4,8,0),(33,4,3,0),(33,4,0,0),(33,5,10,0),(33,5,3,0),(33,5,2,0),(33,5,1,0),(33,5,0,0),(34,5,11,0),(33,13,10,0),(33,13,9,0),(33,13,3,0),(33,13,1,0),(34,13,4,0),(33,12,9,0),(33,12,3,0),(33,8,9,0),(33,8,6,0),(33,8,3,0),(33,8,0,0),(34,8,11,0),(33,7,9,0),(33,7,2,0),(33,7,0,0),(34,7,4,0),(33,3,0,0),(34,3,4,0),(33,2,10,0),(33,2,9,0),(33,2,11,0),(33,2,1,0),(34,2,12,0),(33,1,10,0),(33,1,0,0),(34,1,6,0),(33,0,11,0),(33,0,12,0),(34,0,3,0)]
def rawNew : List Gate := [(33,10,2,0),(33,10,3,0),(33,0,10,0),(33,3,10,0),(33,2,3,0),(49,0,1,2),(33,2,3,0),(33,0,1,0),(33,0,4,0),(33,0,6,0),(33,0,11,0),(49,2,3,0),(33,0,11,0),(33,0,6,0),(33,0,4,0),(33,0,3,0),(33,0,4,0),(33,0,6,0),(33,0,11,0),(49,7,8,0),(33,0,11,0),(33,0,6,0),(33,0,4,0),(33,0,3,0),(33,0,1,0),(33,4,3,0),(33,4,1,0),(33,4,0,0),(33,0,12,0),(33,0,8,0),(33,0,3,0),(33,0,2,0),(33,12,7,0),(33,12,1,0),(33,12,0,0),(33,6,12,0),(33,6,3,0),(33,5,12,0),(33,5,8,0),(34,5,12,0),(33,8,1,0),(34,8,4,0),(33,13,4,0),(33,13,3,0),(34,13,6,0),(33,11,4,0),(33,11,2,0),(34,11,8,0),(33,1,7,0),(33,1,2,0),(34,1,6,0),(33,7,6,0),(33,7,5,0),(34,7,11,0),(33,2,3,0),(34,2,12,0),(33,3,5,0),(34,3,11,0),(33,9,6,0),(34,9,5,0),(33,10,3,0),(33,10,6,0),(33,10,9,0),(33,10,12,0)]
def flatOld : List Gate := [(49,0,1,10),(33,1,0,0),(33,10,2,0),(33,10,3,0),(33,0,1,0),(33,4,1,0),(33,1,4,0),(33,11,4,0),(33,4,11,0),(33,6,11,0),(33,11,6,0),(33,10,6,0),(33,6,10,0),(49,2,3,10),(33,6,2,0),(33,6,3,0),(33,10,6,0),(33,10,2,0),(33,6,10,0),(33,6,2,0),(33,2,10,0),(33,2,6,0),(49,7,8,10),(33,10,6,0),(33,10,2,0),(33,10,7,0),(33,10,3,0),(33,6,2,0),(33,6,11,0),(33,6,4,0),(33,6,1,0),(33,6,8,0),(33,6,7,0),(33,2,10,0),(33,2,13,0),(33,2,8,0),(33,2,7,0),(33,2,3,0),(33,2,0,0),(33,9,10,0),(33,9,3,0),(33,9,0,0),(33,11,6,0),(33,11,2,0),(33,11,13,0),(33,11,8,0),(33,11,0,0),(33,4,10,0),(33,4,8,0),(33,4,7,0),(33,4,3,0),(33,4,0,0),(33,1,10,0),(33,1,6,0),(33,1,8,0),(33,1,3,0),(33,5,6,0),(33,5,8,0),(33,13,6,0),(33,13,2,0),(33,13,8,0),(33,13,0,0),(33,12,6,0),(33,12,7,0),(33,12,0,0),(33,8,0,0),(33,7,10,0),(33,7,6,0),(33,7,13,0),(33,7,3,0),(33,3,10,0),(33,3,0,0),(33,0,13,0),(33,0,7,0)]
def flatNew : List Gate := [(33,10,2,0),(33,10,3,0),(33,0,10,0),(33,3,10,0),(33,2,3,0),(49,0,1,2),(33,2,3,0),(33,0,1,0),(33,0,4,0),(33,0,6,0),(33,0,11,0),(49,2,3,0),(33,0,11,0),(33,0,6,0),(33,0,4,0),(33,0,3,0),(33,0,4,0),(33,0,6,0),(33,0,11,0),(49,7,8,0),(33,0,11,0),(33,0,6,0),(33,0,4,0),(33,0,3,0),(33,0,1,0),(33,4,3,0),(33,4,1,0),(33,4,0,0),(33,0,12,0),(33,0,8,0),(33,0,3,0),(33,0,2,0),(33,12,7,0),(33,12,1,0),(33,12,0,0),(33,6,12,0),(33,6,3,0),(33,5,12,0),(33,5,8,0),(33,8,1,0),(33,13,8,0),(33,13,3,0),(33,11,8,0),(33,11,2,0),(33,1,7,0),(33,1,2,0),(33,7,1,0),(33,7,12,0),(33,2,3,0),(33,3,12,0),(33,9,1,0),(33,10,7,0),(33,10,1,0),(33,10,12,0),(33,10,2,0),(34,0,12,0),(34,13,2,0),(34,7,0,0),(34,1,3,0),(34,4,1,0),(34,11,4,0),(34,7,6,0),(34,11,13,0),(34,11,7,0)]
theorem raw_exact_anf : run rawOld = run rawNew := by decide
theorem flat_exact_anf : run flatOld = run flatNew := by decide
theorem exact_gate_counts :
  rawOld.length = 100 ∧ rawNew.length = 64 ∧
  flatOld.length = 74 ∧ flatNew.length = 64 := by decide

#print axioms common_factor
#print axioms rank_two
#print axioms observer_debt
#print axioms observed_group_exact
#print axioms pivot_independence
#print axioms kernel_independence
#print axioms kernel_valid
#print axioms four_output_cosets
#print axioms no_eight_support
#print axioms nine_support_certificate
#print axioms raw_exact_anf
#print axioms flat_exact_anf
#print axioms exact_gate_counts
end Rank99MultiGroup
