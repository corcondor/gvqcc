import Std

namespace GVQCC.ScopeDualQuotient

def parity : List Bool → Bool
  | [] => false
  | a :: xs => Bool.xor a (parity xs)

theorem debt_pair (p m n : Bool) :
    Bool.xor (p && m) (p && n) = (p && Bool.xor m n) := by
  cases p <;> cases m <;> cases n <;> decide

theorem debt_list (p : Bool) (ms : List Bool) :
    parity (ms.map (fun m => p && m)) = (p && parity ms) := by
  induction ms with
  | nil => cases p <;> decide
  | cons a xs ih =>
    change Bool.xor (p && a) (parity (xs.map (fun m => p && m))) =
      (p && Bool.xor a (parity xs))
    rw [ih, debt_pair]

theorem repay_two (p m n v w : Bool) :
    Bool.xor
      (Bool.xor (m && Bool.xor v p) (n && Bool.xor w p))
      (p && Bool.xor m n) =
    Bool.xor (m && v) (n && w) := by
  cases p <;> cases m <;> cases n <;> cases v <;> cases w <;> decide

theorem cx_delta (a b p d e : Bool) :
    Bool.xor (Bool.xor b (p && e)) (Bool.xor a (p && d)) =
      Bool.xor (Bool.xor b a) (p && Bool.xor e d) := by
  cases a <;> cases b <;> cases p <;> cases d <;> cases e <;> decide

theorem ccx_untouched_controls (a b t p d : Bool) :
    Bool.xor (Bool.xor t (p && d)) (a && b) =
      Bool.xor (Bool.xor t (a && b)) (p && d) := by
  cases a <;> cases b <;> cases t <;> cases p <;> cases d <;> decide

theorem snapshot_inactive (active guard : Bool) :
    (active && guard && false) = false := by
  cases active <;> cases guard <;> decide

def guarded {S : Type} (g : Bool) (f : S → S) (x : S) : S :=
  if g then f x else x

theorem guarded_involution {S : Type} (g : Bool) (f : S → S)
    (h : ∀ x, f (f x) = x) (x : S) :
    guarded g f (guarded g f x) = x := by
  cases g <;> simp [guarded, h]

def run {S : Type} (gs : List (S → S)) (x : S) : S :=
  gs.foldl (fun a f => f a) x

theorem run_append {S : Type} (a b : List (S → S)) (x : S) :
    run (a ++ b) x = run b (run a x) := by
  simp [run, List.foldl_append]

theorem inverse_replay {S : Type} (gs : List (S → S))
    (h : ∀ g ∈ gs, ∀ x, g (g x) = x) (x : S) :
    run gs.reverse (run gs x) = x := by
  induction gs generalizing x with
  | nil => rfl
  | cons g gs ih =>
    have hg : ∀ y, g (g y) = y := h g (by simp)
    have ht : ∀ f ∈ gs, ∀ y, f (f y) = y := by
      intro f hf y
      exact h f (by simp [hf]) y
    change run (g :: gs).reverse (run gs (g x)) = x
    rw [List.reverse_cons, run_append, ih ht (g x)]
    exact hg x

def firstRows : List Nat := [2463,6329,471,1802,4113,6434,2570,256,174,6617,4565,4367,5686]
def firstInverse : List Nat := [4668,305,6299,1571,5913,7196,7838,661,128,8170,6256,6328,1333]

def dot (a b : Nat) : Bool :=
  parity ((List.range 13).map (fun i => a.testBit i && b.testBit i))

def applyRows (rows : List Nat) (x : Nat) : Nat :=
  (List.range 13).foldl (fun s i => s + if dot (rows[i]?.getD 0) x then 2^i else 0) 0

theorem first_inverse_certificate :
    (List.range 13).all (fun i => applyRows firstInverse (applyRows firstRows (2^i)) == 2^i) = true := by decide

theorem first_direction_certificate :
    applyRows firstRows 4170 = 2576 ∧
      (4170 : Nat).testBit 0 = false ∧ (4170 : Nat).testBit 2 = false := by decide

abbrev G := Nat × Nat × Nat × Nat

def second : List G :=
  [(49,0,1,10),(33,1,0,0),(34,1,2,0),(33,10,1,0),(34,2,3,0),(33,10,2,0),(34,3,7,0),(34,7,8,0),(34,8,12,0),(34,12,13,0),(34,13,5,0),(33,0,5,0),(33,4,5,0),(33,5,4,0),(33,11,4,0),(33,4,11,0),(33,6,11,0),(34,6,9,0),(33,11,9,0),(33,10,9,0),(33,9,10,0),(49,1,2,10),(33,9,1,0),(33,9,2,0),(33,10,9,0),(33,10,1,0),(33,9,10,0),(33,9,1,0),(34,11,6,0),(34,4,6,0),(34,5,6,0),(34,13,6,0),(34,12,6,0),(34,8,6,0),(34,7,6,0),(34,3,6,0),(34,2,6,0),(33,1,10,0),(33,1,9,0),(34,1,6,0),(49,2,3,10),(33,10,9,0),(33,10,6,0),(33,10,2,0),(33,10,1,0),(33,9,6,0),(33,9,4,0),(33,9,5,0),(33,9,13,0),(33,9,3,0),(33,9,2,0),(33,6,10,0),(33,6,8,0),(33,6,3,0),(33,6,2,0),(33,6,1,0),(33,6,0,0),(33,11,10,0),(33,11,1,0),(33,11,0,0),(33,4,9,0),(33,4,6,0),(33,4,8,0),(33,4,3,0),(33,4,0,0),(33,5,10,0),(33,5,3,0),(33,5,2,0),(33,5,1,0),(33,5,0,0),(34,5,11,0),(33,13,10,0),(33,13,9,0),(33,13,3,0),(33,13,1,0),(34,13,4,0),(33,12,9,0),(33,12,3,0),(33,8,9,0),(33,8,6,0),(33,8,3,0),(33,8,0,0),(34,8,11,0),(33,7,9,0),(33,7,2,0),(33,7,0,0),(34,7,4,0),(33,3,0,0),(34,3,4,0),(33,2,10,0),(33,2,9,0),(33,2,11,0),(33,2,1,0),(34,2,12,0),(33,1,10,0),(33,1,0,0),(34,1,6,0),(33,0,11,0),(33,0,12,0),(34,0,3,0)]

def gate (s : Nat) (g : G) : Nat :=
  let (o,a,b,t) := g
  if o == 49 then
    if s.testBit a && s.testBit b then Nat.xor s (2^t) else s
  else if o == 33 then
    if s.testBit a then Nat.xor s (2^b) else s
  else
    if Bool.xor (s.testBit a) (s.testBit b) then Nat.xor s (2^a + 2^b) else s

def expanded (x : Nat) : Nat := x % 1024 + (x / 1024) * 2048
def actualSecond (x : Nat) : Nat := second.foldl gate (expanded x)
def projected (x : Nat) : Nat :=
  let s := actualSecond x
  s % 1024 + (s / 2048) * 1024

theorem second_collision :
    (8 : Nat) ≠ 132 ∧ projected 8 = 3144 ∧ projected 132 = 3144 ∧
      (actualSecond 8).testBit 10 = true ∧
      (actualSecond 132).testBit 10 = false := by decide

#print axioms debt_pair
#print axioms debt_list
#print axioms repay_two
#print axioms cx_delta
#print axioms ccx_untouched_controls
#print axioms snapshot_inactive
#print axioms guarded_involution
#print axioms run_append
#print axioms inverse_replay
#print axioms first_inverse_certificate
#print axioms first_direction_certificate
#print axioms second_collision
end GVQCC.ScopeDualQuotient
