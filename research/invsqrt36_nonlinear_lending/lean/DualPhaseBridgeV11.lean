import Std.Tactic.BVDecide

/-! Actual V11 dual-measurement and grouped-phase gate lists.
The HMR outcome and both independent classical guards are arbitrary.
No reachability assumptions, no axiom/sorry. Native parser, whole-oracle
composition, and expected execution weights are independently checked.
-/
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.DualPhaseBridgeV11
inductive Gate where
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  | swap (a b : Nat)
  | hmr (q : Nat)
  | cz (a b g : Nat)
  | ccz (a b c g : Nat)
  deriving DecidableEq, Repr
structure State where
  wires : BitVec 37
  phase : Bool
  deriving DecidableEq, Repr
def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) := s ^^^ (v <<< q)
def clearWire (s : BitVec 37) (q : Nat) := s &&& ~~~((1 : BitVec 37) <<< q)
def enabled (a b m : Bool) (g : Nat) : Bool :=
  if g == 0 then true else if g == 1 then a else if g == 2 then b else m
def step (a b m : Bool) (s : State) : Gate → State
  | .cx u t => {s with wires := toggle s.wires t (bit s.wires u)}
  | .ccx u v t => {s with wires := toggle s.wires t (bit s.wires u &&& bit s.wires v)}
  | .swap u v =>
    let d := bit s.wires u ^^^ bit s.wires v
    {s with wires := toggle (toggle s.wires u d) v d}
  | .hmr q =>
    {wires := clearWire s.wires q, phase := Bool.xor s.phase (m && (bit s.wires q).getLsbD 0)}
  | .cz u v g =>
    {s with phase := Bool.xor s.phase (enabled a b m g && (bit s.wires u &&& bit s.wires v).getLsbD 0)}
  | .ccz u v w g =>
    {s with phase := Bool.xor s.phase (enabled a b m g && (bit s.wires u &&& bit s.wires v &&& bit s.wires w).getLsbD 0)}
def run (gs : List Gate) (a b m : Bool) (s : State) := gs.foldl (step a b m) s
def paid (gs : List Gate) : Nat := (gs.filter fun g => match g with | .ccx _ _ _ | .ccz _ _ _ _ => true | _ => false).length
def hmrCount (gs : List Gate) : Nat := (gs.filter fun g => match g with | .hmr _ => true | _ => false).length
def wireOK : Gate → Bool
  | .hmr a => decide (a < 36)
  | .cx a b | .swap a b | .cz a b _ => decide (a < 36 ∧ b < 36 ∧ a ≠ b)
  | .ccx a b c | .ccz a b c _ => decide (a < 36 ∧ b < 36 ∧ c < 36 ∧ a ≠ b ∧ a ≠ c ∧ b ≠ c)
-- Generic two-guard factor identity, separate from the concrete certificates.
theorem commonPhase (a b l₁ l₂ g₁ g₂ : Bool) :
    Bool.xor (a && b && g₁ && l₁) (a && b && g₂ && l₂) =
    (a && b && Bool.xor (g₁ && l₁) (g₂ && l₂)) := by
  cases a <;> cases b <;> cases l₁ <;> cases l₂ <;> cases g₁ <;> cases g₂ <;> decide

def old_dual : List Gate := [.ccx 19 20 33, .cx 18 33, .cx 19 33, .cx 21 19, .swap 29 33, .hmr 29]
def new_dual : List Gate := [.cx 18 33, .cx 19 33, .cx 21 19, .swap 29 33, .hmr 29, .cx 21 19, .cz 19 20 3, .cx 21 19]
theorem eq_dual (s : BitVec 37) (p a b m : Bool) :
    run old_dual a b m ⟨s,p⟩ = run new_dual a b m ⟨s,p⟩ := by
  simp only [old_dual, new_dual, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resources_dual : paid old_dual = 1 ∧ paid new_dual = 0 ∧ hmrCount old_dual = hmrCount new_dual ∧ old_dual.all wireOK = true ∧ new_dual.all wireOK = true := by decide

def old_cost_guard : List Gate := [.ccx 26 31 27, .cz 27 29 1, .cz 15 28 2, .cz 15 13 2, .cz 15 24 2, .cz 15 25 2, .cz 15 35 2, .cz 27 28 2, .cz 27 24 2, .cz 27 33 2, .cz 27 23 2, .cz 27 2 2, .ccx 26 31 27]
def new_cost_guard : List Gate := [.cz 27 29 1, .cz 15 28 2, .cz 15 13 2, .cz 15 24 2, .cz 15 25 2, .cz 15 35 2, .cz 27 28 2, .cz 27 24 2, .cz 27 33 2, .cz 27 23 2, .cz 27 2 2, .ccz 26 31 29 1, .cx 23 2, .cx 24 2, .cx 28 2, .cx 33 2, .ccz 26 31 2 2, .cx 33 2, .cx 28 2, .cx 24 2, .cx 23 2]
theorem eq_cost_guard (s : BitVec 37) (p a b m : Bool) :
    run old_cost_guard a b m ⟨s,p⟩ = run new_cost_guard a b m ⟨s,p⟩ := by
  simp only [old_cost_guard, new_cost_guard, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resources_cost_guard : paid old_cost_guard = 2 ∧ paid new_cost_guard = 2 ∧ hmrCount old_cost_guard = hmrCount new_cost_guard ∧ old_cost_guard.all wireOK = true ∧ new_cost_guard.all wireOK = true := by decide

def old_wide_guard : List Gate := [.ccx 4 25 35, .cz 35 0 1, .cz 31 3 2, .cz 31 6 2, .cz 31 7 2, .cz 31 17 2, .cz 31 20 2, .cz 35 3 2, .cz 35 7 2, .cz 35 12 2, .cz 35 13 2, .cz 35 28 2, .ccx 4 25 35]
def new_wide_guard : List Gate := [.cz 35 0 1, .cz 31 3 2, .cz 31 6 2, .cz 31 7 2, .cz 31 17 2, .cz 31 20 2, .cz 35 3 2, .cz 35 7 2, .cz 35 12 2, .cz 35 13 2, .cz 35 28 2, .ccz 4 25 0 1, .cx 7 3, .cx 12 3, .cx 13 3, .cx 28 3, .ccz 4 25 3 2, .cx 28 3, .cx 13 3, .cx 12 3, .cx 7 3]
theorem eq_wide_guard (s : BitVec 37) (p a b m : Bool) :
    run old_wide_guard a b m ⟨s,p⟩ = run new_wide_guard a b m ⟨s,p⟩ := by
  simp only [old_wide_guard, new_wide_guard, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resources_wide_guard : paid old_wide_guard = 2 ∧ paid new_wide_guard = 2 ∧ hmrCount old_wide_guard = hmrCount new_wide_guard ∧ old_wide_guard.all wireOK = true ∧ new_wide_guard.all wireOK = true := by decide

def old_cost_batch : List Gate := [.ccx 5 19 33, .cz 17 33 0, .cz 33 34 0, .cz 17 31 0, .cz 34 31 0, .cz 17 16 0, .cz 34 16 0, .cz 17 18 0, .cz 34 18 0, .cz 17 0 0, .cz 34 0 0, .cz 17 2 0, .cz 34 2 0, .cz 17 15 0, .cz 34 15 0, .cz 17 19 0, .cz 34 19 0, .cz 17 22 0, .cz 34 22 0, .ccx 5 19 33]
def new_cost_batch : List Gate := [.cz 17 33 0, .cz 33 34 0, .cz 17 31 0, .cz 34 31 0, .cz 17 16 0, .cz 34 16 0, .cz 17 18 0, .cz 34 18 0, .cz 17 0 0, .cz 34 0 0, .cz 17 2 0, .cz 34 2 0, .cz 17 15 0, .cz 34 15 0, .cz 17 19 0, .cz 34 19 0, .cz 17 22 0, .cz 34 22 0, .cx 34 17, .ccz 5 19 17 0, .cx 34 17]
theorem eq_cost_batch (s : BitVec 37) (p a b m : Bool) :
    run old_cost_batch a b m ⟨s,p⟩ = run new_cost_batch a b m ⟨s,p⟩ := by
  simp only [old_cost_batch, new_cost_batch, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resources_cost_batch : paid old_cost_batch = 2 ∧ paid new_cost_batch = 1 ∧ hmrCount old_cost_batch = hmrCount new_cost_batch ∧ old_cost_batch.all wireOK = true ∧ new_cost_batch.all wireOK = true := by decide

def old_wide_batch : List Gate := [.ccx 24 28 7, .cz 3 7 0, .cz 7 9 0, .cz 3 13 0, .cz 9 13 0, .cz 3 17 0, .cz 9 17 0, .cz 3 19 0, .cz 9 19 0, .cz 3 21 0, .cz 9 21 0, .cz 3 25 0, .cz 9 25 0, .cz 3 26 0, .cz 9 26 0, .cz 3 28 0, .cz 9 28 0, .cz 3 33 0, .cz 9 33 0, .ccx 24 28 7]
def new_wide_batch : List Gate := [.cz 3 7 0, .cz 7 9 0, .cz 3 13 0, .cz 9 13 0, .cz 3 17 0, .cz 9 17 0, .cz 3 19 0, .cz 9 19 0, .cz 3 21 0, .cz 9 21 0, .cz 3 25 0, .cz 9 25 0, .cz 3 26 0, .cz 9 26 0, .cz 3 28 0, .cz 9 28 0, .cz 3 33 0, .cz 9 33 0, .cx 9 3, .ccz 24 28 3 0, .cx 9 3]
theorem eq_wide_batch (s : BitVec 37) (p a b m : Bool) :
    run old_wide_batch a b m ⟨s,p⟩ = run new_wide_batch a b m ⟨s,p⟩ := by
  simp only [old_wide_batch, new_wide_batch, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resources_wide_batch : paid old_wide_batch = 2 ∧ paid new_wide_batch = 1 ∧ hmrCount old_wide_batch = hmrCount new_wide_batch ∧ old_wide_batch.all wireOK = true ∧ new_wide_batch.all wireOK = true := by decide

end GVQCC.DualPhaseBridgeV11
