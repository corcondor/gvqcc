import Init

/-!
Minimal *basis-state* formal semantics for the measurement-free KickMix subset.
X/CX/CCX are reversible permutations; Z/CZ/CCZ contribute a Boolean minus sign.
HMR, resets, conditions and Z_POW are outside this model and must be verified
independently by the native KickMix / phase-coefficient checker.

The solver emits concrete Lean `example`s of equality for all 2^n basis
assignments to a <=6-qubit window. Its `cases ...; decide` proofs are checked
by the Lean kernel and cannot rely on a Python truth-table assertion.
-/
namespace GVQCCLean

inductive Gate where
  | x (q : Nat)
  | cx (control target : Nat)
  | ccx (a b target : Nat)
  | z (q : Nat)
  | cz (a b : Nat)
  | ccz (a b c : Nat)
  deriving Repr, DecidableEq

structure Basis where
  bits : Array Bool
  minus : Bool
  deriving Repr, DecidableEq

def init (l : List Bool) : Basis := ⟨l.toArray, false⟩
def readBit (s : Basis) (i : Nat) : Bool := s.bits[i]!
def toggle (s : Basis) (i : Nat) (v : Bool) : Basis :=
  {s with bits := s.bits.set! i (Bool.xor (readBit s i) v)}
def phaseFlip (s : Basis) (v : Bool) : Basis :=
  {s with minus := Bool.xor s.minus v}

def step (s : Basis) : Gate → Basis
  | .x t => toggle s t true
  | .cx c t => toggle s t (readBit s c)
  | .ccx a b t => toggle s t (readBit s a && readBit s b)
  | .z q => phaseFlip s (readBit s q)
  | .cz a b => phaseFlip s (readBit s a && readBit s b)
  | .ccz a b c => phaseFlip s ((readBit s a && readBit s b) && readBit s c)

def run (ops : List Gate) (s : Basis) : Basis := ops.foldl step s

def ccxCost : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: rest => 1 + ccxCost rest
  | _ :: rest => ccxCost rest

-- KickMix assigns three-qubit CCX and CCZ the same Toffoli-like cost.
def nonCliffordCost : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ :: rest => 1 + nonCliffordCost rest
  | .ccz _ _ _ :: rest => 1 + nonCliffordCost rest
  | _ :: rest => nonCliffordCost rest

-- Cross-output product reuse. Valid for *arbitrary* input/target bits.
private def oldFanout : List Gate := [.ccx 0 1 2, .ccx 0 1 3]
private def newFanout : List Gate := [.cx 2 3, .ccx 0 1 2, .cx 2 3]

theorem fanout_exact (a b x y : Bool) :
    run oldFanout (init [a,b,x,y]) = run newFanout (init [a,b,x,y]) := by
  cases a <;> cases b <;> cases x <;> cases y <;> decide

theorem fanout_saved_ccx : ccxCost oldFanout = ccxCost newFanout + 1 := by
  decide

-- Cross-control product fusion. Neither controls nor targets are assumed zero.
private def oldFactor : List Gate := [.ccx 0 1 3, .ccx 0 2 3]
private def newFactor : List Gate := [.cx 1 2, .ccx 0 2 3, .cx 1 2]

theorem factor_exact (a b c t : Bool) :
    run oldFactor (init [a,b,c,t]) = run newFactor (init [a,b,c,t]) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem factor_saved_ccx : ccxCost oldFactor = ccxCost newFactor + 1 := by
  decide

-- Phase gate semantics are tracked explicitly; equality is stronger than
-- matching output bits alone.
private def oldPhase : List Gate := [.ccx 0 1 2, .cz 2 3, .ccx 0 1 2]
private def newPhase : List Gate := [.cz 2 3, .ccz 0 1 3]

theorem phase_folding_exact (a b c d : Bool) :
    run oldPhase (init [a,b,c,d]) = run newPhase (init [a,b,c,d]) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem phase_folding_saved_nonclifford : nonCliffordCost oldPhase = nonCliffordCost newPhase + 1 := by
  decide

end GVQCCLean
