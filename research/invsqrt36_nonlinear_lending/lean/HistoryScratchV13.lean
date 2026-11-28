import Std.Tactic.BVDecide
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.HistoryScratchV13

inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | swap (a b : Nat)
  | ccx (a b t : Nat)
  | hmr (q : Nat)
  | cz (a b guard : Nat)
  | ccz (a b c guard : Nat)
  | rot (q : Nat)
  deriving DecidableEq, Repr

structure State where
  wires : BitVec 37
  phase : Bool
  rotations : List Bool
  deriving DecidableEq, Repr

def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) : BitVec 37 :=
  s ^^^ ((v &&& 1) <<< q)
def clearWire (s : BitVec 37) (q : Nat) :=
  s &&& ~~~((1 : BitVec 37) <<< q)
def enabled (a b c d : Bool) (g : Nat) : Bool :=
  if g == 0 then true else if g == 1 then a else if g == 2 then b else if g == 3 then c else d
def step (a b c d m : Bool) (s : State) : Gate → State
  | .x q => {s with wires := toggle s.wires q 1}
  | .cx u t => {s with wires := toggle s.wires t (bit s.wires u)}
  | .ccx u v t => {s with wires := toggle s.wires t (bit s.wires u &&& bit s.wires v)}
  | .swap u v =>
    let v' := bit s.wires u ^^^ bit s.wires v
    {s with wires := toggle (toggle s.wires u v') v v'}
  | .hmr u => ⟨clearWire s.wires u, Bool.xor s.phase (m && (bit s.wires u).getLsbD 0), s.rotations⟩
  | .cz u v g => {s with phase := Bool.xor s.phase (enabled a b c d g && (bit s.wires u &&& bit s.wires v).getLsbD 0)}
  | .ccz u v w g => {s with phase := Bool.xor s.phase (enabled a b c d g && (bit s.wires u &&& bit s.wires v &&& bit s.wires w).getLsbD 0)}
  | .rot q => {s with rotations := s.rotations ++ [(bit s.wires q).getLsbD 0]}
def run (gs : List Gate) (a b c d m : Bool) (s : State) := gs.foldl (step a b c d m) s
def paid (gs : List Gate) : Nat := (gs.filter fun g => match g with | .ccx _ _ _ | .ccz _ _ _ _ => true | _ => false).length
def wireOK (n : Nat) : Gate → Bool
  | .x q | .hmr q | .rot q => decide (q < n)
  | .cx a b | .swap a b | .cz a b _ => decide (a < n ∧ b < n ∧ a ≠ b)
  | .ccx a b c | .ccz a b c _ => decide (a < n ∧ b < n ∧ c < n ∧ a ≠ b ∧ a ≠ c ∧ b ≠ c)

-- Deferred scratch, not parked payload reconstruction. The measured old
-- coordinate is erased while the parked payload remains in the original wire.
theorem delayedScratch (p u v m d : Bool) :
    let orig := (v,p,Bool.xor d (m && u))
    let measured := (p,false,Bool.xor d (m && u))
    let swapped := (measured.2.1,measured.1,measured.2.2)
    (Bool.xor swapped.1 v,swapped.2.1,swapped.2.2) = orig := by
  cases p <;> cases u <;> cases v <;> cases m <;> cases d <;> decide

-- Versioned phase potential; two complementary guards form an exact partition.
theorem complementaryHistory (p g : Bool) :
    (g && p) = Bool.xor p ((!g) && p) := by bv_decide
theorem dirtyCubic (a b c d t : Bool) :
    let d' := Bool.xor d (a && b)
    let t' := Bool.xor t (d' && c)
    let d'' := Bool.xor d' (a && b)
    let t'' := Bool.xor t' (d'' && c)
    (d'',t'') = (d,Bool.xor t (a && b && c)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases t <;> decide

def old_15408 : List Gate := [.cx 12 7, .cx 32 7, .ccx 17 7 26, .cx 32 7, .cx 12 7, .cx 29 7, .ccx 32 7 26, .cx 29 7, .cx 7 26, .cx 17 26, .cx 32 26, .ccx 7 17 0, .ccx 0 32 26, .ccx 7 17 0, .ccx 0 32 26, .ccx 12 17 0, .ccx 0 32 26, .ccx 12 17 0, .ccx 0 32 26]
def new_15408 : List Gate := [.cx 29 7, .ccx 32 7 26, .cx 29 7, .cx 7 26, .cx 32 26, .cx 12 7, .x 32, .x 7, .ccx 17 32 0, .ccx 0 7 26, .ccx 17 32 0, .ccx 0 7 26, .x 7, .x 32, .cx 12 7]
theorem eq_15408 (s : BitVec 37) (p a b c d m : Bool) :
    run old_15408 a b c d m ⟨s,p,[]⟩ = run new_15408 a b c d m ⟨s,p,[]⟩ := by
  simp only [old_15408, new_15408, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resource_15408 : old_15408.all (wireOK 36) = true ∧ new_15408.all (wireOK 36) = true ∧
    paid old_15408 = 10 ∧ paid new_15408 = 5 ∧ old_15408.length = 19 ∧ new_15408.length = 15 := by decide

def old_15733 : List Gate := [.cx 7 6, .cx 33 6, .ccx 12 6 26, .cx 33 6, .cx 7 6, .cx 32 7, .ccx 33 7 26, .cx 32 7, .cx 7 26, .cx 12 26, .cx 33 26, .ccx 6 12 0, .ccx 0 33 26, .ccx 6 12 0, .ccx 0 33 26, .ccx 7 12 0, .ccx 0 33 26, .ccx 7 12 0, .ccx 0 33 26]
def new_15733 : List Gate := [.cx 32 7, .ccx 33 7 26, .cx 32 7, .cx 7 26, .cx 33 26, .cx 7 6, .x 33, .x 6, .ccx 12 33 0, .ccx 0 6 26, .ccx 12 33 0, .ccx 0 6 26, .x 6, .x 33, .cx 7 6]
theorem eq_15733 (s : BitVec 37) (p a b c d m : Bool) :
    run old_15733 a b c d m ⟨s,p,[]⟩ = run new_15733 a b c d m ⟨s,p,[]⟩ := by
  simp only [old_15733, new_15733, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resource_15733 : old_15733.all (wireOK 36) = true ∧ new_15733.all (wireOK 36) = true ∧
    paid old_15733 = 10 ∧ paid new_15733 = 5 ∧ old_15733.length = 19 ∧ new_15733.length = 15 := by decide

def old_16469 : List Gate := [.cx 12 7, .cx 14 7, .ccx 31 7 30, .cx 14 7, .cx 12 7, .cx 16 7, .ccx 14 7 30, .cx 16 7, .cx 7 30, .cx 14 30, .ccx 7 14 0, .ccx 0 31 30, .ccx 7 14 0, .ccx 0 31 30, .ccx 14 16 0, .ccx 0 31 30, .ccx 14 16 0, .ccx 0 31 30]
def new_16469 : List Gate := [.cx 12 7, .ccx 31 7 30, .cx 12 7, .cx 7 30, .cx 16 7, .x 31, .x 7, .ccx 14 31 0, .ccx 0 7 30, .ccx 14 31 0, .ccx 0 7 30, .x 7, .x 31, .cx 16 7]
theorem eq_16469 (s : BitVec 37) (p a b c d m : Bool) :
    run old_16469 a b c d m ⟨s,p,[]⟩ = run new_16469 a b c d m ⟨s,p,[]⟩ := by
  simp only [old_16469, new_16469, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resource_16469 : old_16469.all (wireOK 36) = true ∧ new_16469.all (wireOK 36) = true ∧
    paid old_16469 = 10 ∧ paid new_16469 = 5 ∧ old_16469.length = 18 ∧ new_16469.length = 14 := by decide

def old_16798 : List Gate := [.cx 24 5, .cx 35 5, .ccx 26 5 29, .cx 35 5, .cx 24 5, .cx 32 24, .ccx 35 24 29, .cx 32 24, .cx 24 29, .cx 26 29, .cx 35 29, .ccx 5 26 0, .ccx 0 35 29, .ccx 5 26 0, .ccx 0 35 29, .ccx 24 26 0, .ccx 0 35 29, .ccx 24 26 0, .ccx 0 35 29]
def new_16798 : List Gate := [.cx 32 24, .ccx 35 24 29, .cx 32 24, .cx 24 29, .cx 35 29, .cx 24 5, .x 35, .x 5, .ccx 26 35 0, .ccx 0 5 29, .ccx 26 35 0, .ccx 0 5 29, .x 5, .x 35, .cx 24 5]
theorem eq_16798 (s : BitVec 37) (p a b c d m : Bool) :
    run old_16798 a b c d m ⟨s,p,[]⟩ = run new_16798 a b c d m ⟨s,p,[]⟩ := by
  simp only [old_16798, new_16798, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem resource_16798 : old_16798.all (wireOK 36) = true ∧ new_16798.all (wireOK 36) = true ∧
    paid old_16798 = 10 ∧ paid new_16798 = 5 ∧ old_16798.length = 19 ∧ new_16798.length = 15 := by decide

-- Actual source [22829,22859), V13 width parent native [15400,15411).
-- q36=0 on entry; the BDD replay verifies the reachable decoder premise.
def old_gap : List Gate := [.swap 26 36, .ccx 29 32 26, .cx 23 26, .cx 32 29, .cx 32 12, .cx 23 29, .cx 23 12, .cx 17 12, .cx 3 12, .hmr 23, .swap 23 36]
def gap_prefix : List Gate := [.cx 32 29, .cx 32 12, .cx 23 29, .cx 23 12, .cx 17 12, .cx 3 12, .hmr 23, .swap 26 23]
def new_gap : List Gate := [.cx 32 29, .cx 32 12, .cx 23 29, .cx 23 12, .cx 17 12, .cx 3 12, .hmr 23, .swap 26 23, .cx 29 7, .ccx 32 7 26, .cx 29 7, .cx 7 26, .cx 32 26, .cx 12 7, .x 32, .x 7, .ccx 17 32 0, .ccx 0 7 26, .ccx 17 32 0, .ccx 0 7 26, .x 7, .x 32, .cx 12 7]

def decode26 (s : BitVec 37) : BitVec 37 :=
  let a := bit s 17
  let b := bit s 32
  let c := bit s 7
  let d := bit s 12
  let e := bit s 29
  (b &&& (c ^^^ e)) ^^^ c ^^^ b ^^^ (a &&& (b ^^^ 1) &&& (c ^^^ d ^^^ 1))

theorem actual_gap (s : BitVec 37) (p m : Bool)
    (zero36 : bit s 36 = 0)
    (reachable : ((bit s 29 &&& bit s 32) ^^^ bit s 23) =
      decode26 (run gap_prefix false false false false m ⟨s,p,[]⟩).wires) :
    run old_gap false false false false m ⟨s,p,[]⟩ =
      run new_gap false false false false m ⟨s,p,[]⟩ := by
  simp only [old_gap, new_gap, gap_prefix, decode26, run, List.foldl_cons, List.foldl_nil, step,
    bit, toggle, clearWire, enabled, State.mk.injEq] at *
  bv_decide

theorem gap_resources :
    old_gap.all (wireOK 37) = true ∧ new_gap.all (wireOK 36) = true ∧
    paid old_gap = 1 ∧ paid new_gap = 5 := by decide

-- Actual cost history splice [11023,11055). The unchanged nested IF 837
-- is flattened to its six guarded CZ instructions for this semantic model.
-- Guard IDs: 1=457, 2=837, 3=460, 4=458. One HMR event 467, one rotation.
-- The actual classical register/guard stack is separately compared by BDD.
def history_scaffold : List Gate := [.cx 23 2, .cx 24 2, .cx 28 2, .cx 33 2, .ccz 26 31 2 2, .cx 33 2, .cx 28 2, .cx 24 2, .cx 23 2, .ccx 0 15 27, .cz 29 27 3, .cz 29 27 4, .cz 29 27 1, .cx 15 27, .cx 8 27, .x 27, .cz 27 29 2, .cz 27 25 2, .cz 27 5 2, .rot 27, .x 27, .cz 28 27 2, .cz 24 27 2, .cz 33 27 2, .cz 23 27 2, .cz 25 27 2, .cz 2 27 2, .hmr 27, .ccx 26 31 27]
def old_history : List Gate := [.ccz 26 31 29 1, .cx 23 2, .cx 24 2, .cx 28 2, .cx 33 2, .ccz 26 31 2 2, .cx 33 2, .cx 28 2, .cx 24 2, .cx 23 2, .ccx 0 15 27, .cz 29 27 3, .cz 29 27 4, .cz 29 27 1, .cx 15 27, .cx 8 27, .x 27, .cz 27 29 2, .cz 27 25 2, .cz 27 5 2, .rot 27, .x 27, .cz 28 27 2, .cz 24 27 2, .cz 33 27 2, .cz 23 27 2, .cz 25 27 2, .cz 2 27 2, .hmr 27, .ccx 26 31 27]
def new_history : List Gate := [.cx 23 2, .cx 24 2, .cx 28 2, .cx 33 2, .ccz 26 31 2 2, .cx 33 2, .cx 28 2, .cx 24 2, .cx 23 2, .ccx 0 15 27, .cz 29 27 3, .cz 29 27 4, .cz 29 27 1, .cx 15 27, .cx 8 27, .x 27, .cz 27 29 2, .cz 27 25 2, .cz 27 5 2, .rot 27, .x 27, .cz 28 27 2, .cz 24 27 2, .cz 33 27 2, .cz 23 27 2, .cz 25 27 2, .cz 2 27 2, .hmr 27, .ccx 26 31 27, .cz 27 29 1]
theorem actual_history (s : BitVec 37) (p a b c d m : Bool) :
    run old_history a b c d m ⟨s,p,[]⟩ =
      run new_history a b c d m ⟨s,p,[]⟩ := by
  simp only [old_history, new_history, run,
    List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, State.mk.injEq]
  bv_decide
theorem history_resources :
    old_history.all (wireOK 36) = true ∧ new_history.all (wireOK 36) = true ∧
    paid old_history = 4 ∧ paid new_history = 3 := by decide

end GVQCC.HistoryScratchV13
