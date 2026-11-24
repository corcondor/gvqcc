import Std.Tactic.BVDecide
set_option maxRecDepth 65536
set_option maxHeartbeats 0

namespace GVQCC.TargetDeltaV9

inductive Gate where
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  deriving DecidableEq, Repr

def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) : BitVec 37 :=
  s ^^^ ((v &&& 1) <<< q)

def step (s : BitVec 37) : Gate → BitVec 37
  | .cx a t => toggle s t (bit s a)
  | .ccx a b t => toggle s t (bit s a &&& bit s b)

def run (gs : List Gate) (s : BitVec 37) : BitVec 37 := gs.foldl step s

def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs

def valid36 : Gate → Bool
  | .cx a t => decide (a < 36 ∧ t < 36 ∧ a ≠ t)
  | .ccx a b t => decide (a < 36 ∧ b < 36 ∧ t < 36 ∧ a ≠ b ∧ a ≠ t ∧ b ≠ t)

-- Actual PR48 native interval [11262,11264), byte-identical to
-- PR45 [11242,11244). No entry-state precondition.
def oldA : List Gate := [.ccx 14 29 21, .ccx 27 29 21]
def newA : List Gate := [.cx 27 14, .ccx 14 29 21, .cx 27 14]

theorem actualA (s : BitVec 37) : run oldA s = run newA s := by
  simp only [oldA, newA, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide

theorem resourceA : oldA.all valid36 = true ∧ newA.all valid36 = true ∧
    paid oldA = 2 ∧ paid newA = 1 := by decide

-- Actual PR48 interval [13624,13628), after two interleaved CX writes.
def oldB : List Gate := [.ccx 29 25 19, .cx 4 3, .cx 27 3, .ccx 3 25 19]
def newB : List Gate := [.cx 4 3, .cx 27 3, .cx 29 3, .ccx 3 25 19, .cx 29 3]

theorem actualB (s : BitVec 37) : run oldB s = run newB s := by
  simp only [oldB, newB, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide

theorem resourceB : oldB.all valid36 = true ∧ newB.all valid36 = true ∧
    paid oldB = 2 ∧ paid newB = 1 := by decide

-- Independent PR44 wide branch [16993,16997); not added to PR48.
def oldC : List Gate := [.ccx 0 33 2, .cx 18 29, .cx 17 29, .ccx 29 33 2]
def newC : List Gate := [.cx 18 29, .cx 17 29, .cx 29 0, .ccx 0 33 2, .cx 29 0]

theorem actualC (s : BitVec 37) : run oldC s = run newC s := by
  simp only [oldC, newC, run, List.foldl_cons, List.foldl_nil, step, bit, toggle]
  bv_decide

theorem resourceC : oldC.all valid36 = true ∧ newC.all valid36 = true ∧
    paid oldC = 2 ∧ paid newC = 1 := by decide

theorem guardedA (s : BitVec 37) (g : Bool) :
    (if g then run oldA s else s) = (if g then run newA s else s) := by
  cases g <;> simp [actualA]

end GVQCC.TargetDeltaV9
