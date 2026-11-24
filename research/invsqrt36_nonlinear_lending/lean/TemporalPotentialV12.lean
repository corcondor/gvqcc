import Std.Tactic.BVDecide
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.TemporalPotentialV12

inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | swap (a b : Nat)
  | ccx (a b t : Nat)
  | z (q g : Nat)
  | cz (a b g : Nat)
  | ccz (a b c g : Nat)
  deriving DecidableEq, Repr
structure State where
  wires : BitVec 37
  phase : Bool
  deriving DecidableEq, Repr
def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) := s ^^^ (v <<< q)
def enabled (g1 g2 : Bool) (g : Nat) : Bool :=
  if g == 0 then true else if g == 1 then g1 else g2
def step (g1 g2 : Bool) (s : State) : Gate → State
  | .x q => {s with wires := toggle s.wires q 1}
  | .cx u t => {s with wires := toggle s.wires t (bit s.wires u)}
  | .ccx u v t => {s with wires := toggle s.wires t (bit s.wires u &&& bit s.wires v)}
  | .swap u v =>
    let d := bit s.wires u ^^^ bit s.wires v
    {s with wires := toggle (toggle s.wires u d) v d}
  | .z u g => {s with phase := Bool.xor s.phase (enabled g1 g2 g && (bit s.wires u).getLsbD 0)}
  | .cz u v g => {s with phase := Bool.xor s.phase (enabled g1 g2 g && (bit s.wires u &&& bit s.wires v).getLsbD 0)}
  | .ccz u v w g => {s with phase := Bool.xor s.phase (enabled g1 g2 g && (bit s.wires u &&& bit s.wires v &&& bit s.wires w).getLsbD 0)}
def run (gs : List Gate) (a b : Bool) (s : State) := gs.foldl (step a b) s
def paid (gs : List Gate) : Nat := (gs.filter fun g => match g with | .ccx _ _ _ | .ccz _ _ _ _ => true | _ => false).length
def wireOK : Gate → Bool
  | .x a | .z a _ => decide (a < 36)
  | .cx a b | .swap a b | .cz a b _ => decide (a < 36 ∧ b < 36 ∧ a ≠ b)
  | .ccx a b c | .ccz a b c _ => decide (a < 36 ∧ b < 36 ∧ c < 36 ∧ a ≠ b ∧ a ≠ c ∧ b ≠ c)

-- The temporal hub does not allocate an extra register: use an existing update
-- as the difference between two quadratic potentials.
theorem temporalDifference (a b c t g : Bool) :
    (g && a && b && c) =
    Bool.xor (g && t && c) (g && Bool.xor t (a && b) && c) := by bv_decide
theorem twoStepTelescoping (t f h c g : Bool) :
    Bool.xor (g && f && c) (g && h && c) =
    Bool.xor (g && t && c) (g && Bool.xor (Bool.xor t f) h && c) := by bv_decide

def old_wide18076 : List Gate := [.cx 26 24, .cx 24 26, .cx 16 26, .cx 8 26, .cx 7 26, .cx 5 26, .swap 29 32, .ccx 24 26 29, .z 15 2, .z 19 2, .cz 16 19 2, .cx 26 29, .cx 16 29, .cx 8 29, .cx 7 29, .cx 16 35, .cx 29 35, .cx 25 29, .cx 8 35, .cx 5 29, .ccx 24 26 5, .ccx 29 35 5, .cx 7 5, .cx 8 5, .cx 16 5, .cx 26 5, .swap 32 5, .cx 25 29, .ccz 24 26 29 1]
def new_wide18076 : List Gate := [.cz 5 24 1, .cx 26 24, .cx 24 26, .cx 16 26, .cx 8 26, .cx 7 26, .cx 5 26, .swap 29 32, .ccx 24 26 29, .cz 5 29 1, .z 15 2, .z 19 2, .cz 16 19 2, .cx 26 29, .cx 16 29, .cx 8 29, .cx 7 29, .cx 16 35, .cx 29 35, .cx 25 29, .cx 8 35, .cx 5 29, .ccx 24 26 5, .cz 5 25 1, .cz 5 29 1, .ccx 29 35 5, .cx 7 5, .cx 8 5, .cx 16 5, .cx 26 5, .swap 32 5, .cx 25 29]
theorem eq_wide18076 (s : BitVec 37) (p a b : Bool) :
    run old_wide18076 a b ⟨s,p⟩ = run new_wide18076 a b ⟨s,p⟩ := by
  simp only [old_wide18076, new_wide18076, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, enabled, State.mk.injEq]
  bv_decide
theorem res_wide18076 : old_wide18076.all wireOK = true ∧ new_wide18076.all wireOK = true ∧
    paid old_wide18076 = 4 ∧ paid new_wide18076 = 3 ∧
    old_wide18076.length = 29 ∧ new_wide18076.length = 32 := by decide

def old_wide18895 : List Gate := [.ccx 24 33 26, .z 15 2, .z 27 2, .cz 16 27 2, .cx 24 26, .cx 7 26, .cx 26 32, .cx 25 26, .cx 16 32, .cx 10 32, .cx 9 32, .ccx 24 33 7, .ccx 26 32 7, .cx 24 7, .swap 35 7, .cx 25 26, .ccz 24 26 33 1]
def new_wide18895 : List Gate := [.z 7 1, .cz 7 24 1, .ccx 24 33 26, .cz 7 26 1, .z 15 2, .z 27 2, .cz 16 27 2, .cx 24 26, .cx 7 26, .cx 26 32, .cx 25 26, .cx 16 32, .cx 10 32, .cx 9 32, .ccx 24 33 7, .cz 7 25 1, .cz 7 26 1, .ccx 26 32 7, .cx 24 7, .swap 35 7, .cx 25 26]
theorem eq_wide18895 (s : BitVec 37) (p a b : Bool) :
    run old_wide18895 a b ⟨s,p⟩ = run new_wide18895 a b ⟨s,p⟩ := by
  simp only [old_wide18895, new_wide18895, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, enabled, State.mk.injEq]
  bv_decide
theorem res_wide18895 : old_wide18895.all wireOK = true ∧ new_wide18895.all wireOK = true ∧
    paid old_wide18895 = 4 ∧ paid new_wide18895 = 3 ∧
    old_wide18895.length = 17 ∧ new_wide18895.length = 21 := by decide

def old_wide32299 : List Gate := [.ccz 20 24 28 1, .cz 10 20 1, .cz 14 20 1, .cz 15 20 1, .cz 17 20 1, .cz 20 23 1, .cz 20 24 1, .cz 20 30 1, .cz 20 32 1, .cx 28 2, .cx 26 2, .cx 22 2, .cx 19 2, .cx 18 2, .cx 15 2, .cx 14 2, .cx 13 2, .cx 12 2, .ccx 24 28 2]
def new_wide32299 : List Gate := [.cz 2 20 1, .cz 12 20 1, .cz 13 20 1, .cz 14 20 1, .cz 15 20 1, .cz 18 20 1, .cz 19 20 1, .cz 20 22 1, .cz 20 26 1, .cz 20 28 1, .cz 10 20 1, .cz 14 20 1, .cz 15 20 1, .cz 17 20 1, .cz 20 23 1, .cz 20 24 1, .cz 20 30 1, .cz 20 32 1, .cx 28 2, .cx 26 2, .cx 22 2, .cx 19 2, .cx 18 2, .cx 15 2, .cx 14 2, .cx 13 2, .cx 12 2, .ccx 24 28 2, .cz 2 20 1]
theorem eq_wide32299 (s : BitVec 37) (p a b : Bool) :
    run old_wide32299 a b ⟨s,p⟩ = run new_wide32299 a b ⟨s,p⟩ := by
  simp only [old_wide32299, new_wide32299, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, enabled, State.mk.injEq]
  bv_decide
theorem res_wide32299 : old_wide32299.all wireOK = true ∧ new_wide32299.all wireOK = true ∧
    paid old_wide32299 = 2 ∧ paid new_wide32299 = 1 ∧
    old_wide32299.length = 19 ∧ new_wide32299.length = 29 := by decide

def old_wordCost14168 : List Gate := [.z 34 1, .cx 34 32, .z 32 1, .cx 34 32, .cx 8 32, .cz 34 32 1, .cx 34 32, .cx 8 32, .cz 34 32 1]
def new_wordCost14168 : List Gate := [.cx 34 32, .z 32 1, .cz 8 34 1]
theorem eq_wordCost14168 (s : BitVec 37) (p a b : Bool) :
    run old_wordCost14168 a b ⟨s,p⟩ = run new_wordCost14168 a b ⟨s,p⟩ := by
  simp only [old_wordCost14168, new_wordCost14168, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, enabled, State.mk.injEq]
  bv_decide
theorem res_wordCost14168 : old_wordCost14168.all wireOK = true ∧ new_wordCost14168.all wireOK = true ∧
    paid old_wordCost14168 = 0 ∧ paid new_wordCost14168 = 0 ∧
    old_wordCost14168.length = 9 ∧ new_wordCost14168.length = 3 := by decide

def old_wordCost15316 : List Gate := [.z 20 1, .cx 20 25, .cx 25 20, .cx 9 20, .cz 25 20 1, .cx 25 20, .cx 9 20, .cz 25 20 1, .cx 20 25]
def new_wordCost15316 : List Gate := [.z 25 1, .cz 9 20 1, .cz 9 25 1]
theorem eq_wordCost15316 (s : BitVec 37) (p a b : Bool) :
    run old_wordCost15316 a b ⟨s,p⟩ = run new_wordCost15316 a b ⟨s,p⟩ := by
  simp only [old_wordCost15316, new_wordCost15316, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, enabled, State.mk.injEq]
  bv_decide
theorem res_wordCost15316 : old_wordCost15316.all wireOK = true ∧ new_wordCost15316.all wireOK = true ∧
    paid old_wordCost15316 = 0 ∧ paid new_wordCost15316 = 0 ∧
    old_wordCost15316.length = 9 ∧ new_wordCost15316.length = 3 := by decide

def old_wordWide17347 : List Gate := [.z 24 1, .cx 24 7, .cx 7 24, .cx 6 24, .cz 7 24 1, .cx 7 24, .cx 6 24, .cz 7 24 1, .cx 24 7]
def new_wordWide17347 : List Gate := [.z 7 1, .cz 6 7 1, .cz 6 24 1]
theorem eq_wordWide17347 (s : BitVec 37) (p a b : Bool) :
    run old_wordWide17347 a b ⟨s,p⟩ = run new_wordWide17347 a b ⟨s,p⟩ := by
  simp only [old_wordWide17347, new_wordWide17347, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, enabled, State.mk.injEq]
  bv_decide
theorem res_wordWide17347 : old_wordWide17347.all wireOK = true ∧ new_wordWide17347.all wireOK = true ∧
    paid old_wordWide17347 = 0 ∧ paid new_wordWide17347 = 0 ∧
    old_wordWide17347.length = 9 ∧ new_wordWide17347.length = 3 := by decide

-- Conditional representative: the actual reachability premise is discharged
-- by independent BDD, not by the following universal Boolean implication.
theorem reachablePhase (a b c p g : Bool) (h : (a && b) = p) :
    (g && a && b && c) = (g && p && c) := by bv_decide

end GVQCC.TemporalPotentialV12
