import Std
set_option maxRecDepth 10000
set_option maxHeartbeats 0
namespace V16Counterexample

-- Restricted interpreter for the actual frozen gate lists below.
-- Reachability of the witness is established independently by full-domain BDD.
inductive Gate where
  | cx (a b : Nat)
  | swap (a b : Nat)
  | z (a : Nat) (c : Option Nat)
  | cz (a b : Nat) (c : Option Nat)
  | ccz (a b c : Nat)
  | guard (c : Nat)
  | endGuard
  | clear (c : Nat)

structure State where
  q : Nat
  c805 : Bool
  c837 : Bool
  phase : Bool
  active : Bool
  stack : List Bool
  deriving DecidableEq

def bit (s : State) (i : Nat) : Bool := s.q.testBit i
def ctl (s : State) (c : Nat) : Bool := if c == 805 then s.c805 else s.c837
def enabled (s : State) (c : Option Nat) : Bool := s.active && (match c with | none => true | some k => ctl s k)
def flip (s : State) (i : Nat) (f : Bool) : State :=
  if f then {s with q := Nat.xor s.q (Nat.shiftLeft 1 i)} else s
def addPhase (s : State) (f : Bool) : State := {s with phase := Bool.xor s.phase f}
def step (s : State) (g : Gate) : State := match g with
  | .cx a b => flip s b (s.active && bit s a)
  | .swap a b =>
    let f := s.active && Bool.xor (bit s a) (bit s b)
    flip (flip s a f) b f
  | .z a c => addPhase s (enabled s c && bit s a)
  | .cz a b c => addPhase s (enabled s c && bit s a && bit s b)
  | .ccz a b c => addPhase s (s.active && bit s a && bit s b && bit s c)
  | .guard c => {s with active := s.active && ctl s c, stack := s.active :: s.stack}
  | .endGuard => {s with active := s.stack.headD false, stack := s.stack.drop 1}
  | .clear c => if s.active then (if c == 805 then {s with c805 := false} else {s with c837 := false}) else s

def run (s : State) (gs : List Gate) : State := gs.foldl step s

def witness : State := ⟨42198059321, false, true, false, true, []⟩

def oldGates : List Gate := [
  .guard 837,
  .cx 7 13,
  .cx 19 13,
  .cx 31 13,
  .cx 34 13,
  .cx 15 13,
  .cx 11 13,
  .cx 14 13,
  .ccz 29 13 27,
  .cz 13 27 none,
  .cx 14 13,
  .cx 11 13,
  .cx 15 13,
  .cx 34 13,
  .cx 31 13,
  .cx 19 13,
  .cx 7 13,
  .endGuard,
  .cz 21 27 (some 837),
  .cz 21 28 (some 837),
  .cz 21 26 (some 837),
  .cz 21 20 (some 837),
  .cz 21 1 (some 837),
  .cz 21 0 (some 837),
  .cz 21 17 (some 837),
  .cz 21 33 (some 837),
  .cz 21 22 (some 837),
  .cz 21 12 (some 837),
  .cz 21 19 (some 837),
  .cz 21 8 (some 837),
  .cz 21 5 (some 837),
  .cz 21 31 (some 837),
  .cz 21 9 (some 837),
  .cz 21 34 (some 837),
  .cz 21 15 (some 837),
  .cz 27 11 (some 837),
  .clear 805,
  .cx 21 29,
  .cx 26 0,
  .cx 29 21,
  .cx 27 29,
  .cz 28 29 (some 837),
  .cz 24 29 (some 837),
  .cz 18 29 (some 837),
  .cz 1 29 (some 837),
  .cz 17 29 (some 837),
  .cz 33 29 (some 837),
  .cz 22 29 (some 837),
  .cz 25 29 (some 837),
  .cz 35 29 (some 837),
  .cz 5 29 (some 837),
  .cz 2 29 (some 837),
  .cz 11 29 (some 837)
]

def newGates : List Gate := [
  .z 27 (some 805),
  .cz 27 29 (some 805),
  .cx 21 29,
  .swap 14 21,
  .swap 11 14,
  .swap 6 11,
  .swap 15 6,
  .swap 34 15,
  .swap 3 34,
  .swap 2 3,
  .swap 4 2,
  .swap 9 4,
  .swap 31 9,
  .swap 5 31,
  .swap 8 5,
  .swap 19 8,
  .swap 12 19,
  .swap 35 12,
  .swap 32 35,
  .swap 7 32,
  .swap 25 7,
  .swap 22 25,
  .swap 10 22,
  .swap 16 10,
  .swap 23 16,
  .swap 33 23,
  .swap 17 33,
  .cx 0 26,
  .swap 1 17,
  .swap 18 0,
  .swap 24 1,
  .swap 13 18,
  .swap 20 24,
  .cx 26 13,
  .swap 28 20,
  .swap 30 26,
  .cx 29 28,
  .cx 29 27,
  .swap 29 30,
  .cx 27 30,
  .swap 27 29,
  .cz 20 29 (some 837),
  .cz 1 29 (some 837),
  .cz 0 29 (some 837),
  .cz 17 29 (some 837),
  .cz 33 29 (some 837),
  .cz 23 29 (some 837),
  .cz 25 29 (some 837),
  .cz 7 29 (some 837),
  .cz 12 29 (some 837),
  .cz 31 29 (some 837),
  .cz 3 29 (some 837),
  .cz 14 29 (some 837),
  .swap 27 0,
  .swap 30 27,
  .swap 28 21,
  .swap 26 30,
  .swap 20 28,
  .swap 13 26,
  .swap 24 20,
  .swap 18 13,
  .swap 1 24,
  .swap 17 1,
  .swap 33 17,
  .swap 23 33,
  .swap 16 23,
  .swap 10 16,
  .swap 22 10,
  .swap 25 22,
  .swap 7 25,
  .swap 32 7,
  .swap 35 32,
  .swap 12 35,
  .swap 19 12,
  .swap 8 19,
  .swap 5 8,
  .swap 31 5,
  .swap 9 31,
  .swap 4 9,
  .swap 2 4,
  .swap 3 2,
  .swap 34 3,
  .swap 15 34,
  .swap 6 15,
  .swap 11 6,
  .swap 14 11
]

-- Same basis output; different sign for a reachable witness.
-- The theorem is a concrete local refutation, not an end-to-end reachability proof.
theorem actual_phase_counterexample :
    (run witness oldGates).q = 42732833081 ∧
    (run witness newGates).q = 42732833081 ∧
    (run witness oldGates).phase = false ∧
    (run witness newGates).phase = true := by decide

theorem different_phase : (run witness oldGates).phase ≠ (run witness newGates).phase := by decide
end V16Counterexample


namespace V16Counterexample
-- V17: exact published donor lists, fixed classical interface repair only.
def redirectHistory : Gate → Gate
  | .z a (some 805) => .z a (some 837)
  | .cz a b (some 805) => .cz a b (some 837)
  | g => g

def repairedGates : List Gate := newGates.map redirectHistory ++ [.clear 805]

theorem repaired_witness_refutation :
    (run witness oldGates).q = (run witness repairedGates).q ∧
    (run witness oldGates).c805 = (run witness repairedGates).c805 ∧
    (run witness oldGates).c837 = (run witness repairedGates).c837 ∧
    (run witness oldGates).phase ≠ (run witness repairedGates).phase := by decide

def parityOn (q : Nat) (indices : List Nat) : Bool :=
  indices.foldl (fun p i => Bool.xor p (q.testBit i)) false

def residual (s : State) : Bool :=
  let a := parityOn s.q [7,11,13,14,15,19,31,34]
  let b := parityOn s.q [0,1,5,8,9,12,15,17,19,20,22,26,27,28,31,33,34]
  s.c837 && Bool.xor (Bool.xor (s.q.testBit 21 && b)
    (s.q.testBit 27 && s.q.testBit 11))
    (s.q.testBit 27 && !s.q.testBit 29 && !a)

theorem concrete_residual :
    residual witness =
      Bool.xor (run witness oldGates).phase (run witness repairedGates).phase := by decide

theorem repair_length : oldGates.length = 53 ∧ repairedGates.length = 87 := by decide

-- These arithmetic facts are on the independently measured resource receipt,
-- not a Lean proof of BDD reachability or official scoring.
theorem overhead_receipt :
    26687 - 22501 = 4186 ∧
    287 - 161 = 126 ∧ 141 - 22 = 119 ∧
    24347 - 20161 = 4186 := by decide

end V16Counterexample
