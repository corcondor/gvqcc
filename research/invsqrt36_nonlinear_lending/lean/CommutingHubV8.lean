import Std.Tactic.BVDecide

/-! Actual 11 nonlocal commuting hub rewrites in the V8 zero-frame parent
SHA256 43ae51a65ea4161c7ff1a6ab274ebc0bfd84b629a1943d1713e45aac69c241c8.
Candidate f7abc033dbed5477d5685225d9bf5fe262ceb888189ebcc3266ce23f9d15fd6d.
The gate lists are generated from native parsed old/new lists: PUSH/POP
flattened into masks of classical SSA variables, original event IDs recorded
per slice. No slice writes classical bits except unconditional HMR, whose
measurement outcome is independent and supplied by m. Rotation observables
record the activation AND computational value, in unchanged angle order.
Local universal branch equality and wire/paid-resource theorems; not a
full Lean proof of native parsing, reachable zero sets, or numerical oracle.
-/
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.CommutingHubV8

inductive Gate where
  | x (q : Nat) (g : BitVec 8)
  | cx (a t : Nat) (g : BitVec 8)
  | ccx (a b t : Nat) (g : BitVec 8)
  | swap (a b : Nat) (g : BitVec 8)
  | z (q : Nat) (g : BitVec 8)
  | cz (a b : Nat) (g : BitVec 8)
  | ccz (a b c : Nat) (g : BitVec 8)
  | sign (g : BitVec 8)
  | hmr (q eventId : Nat)
  | rot (q index : Nat) (g : BitVec 8)
  deriving DecidableEq, Repr

structure State where
  wires : BitVec 36
  phase : Bool
  rotations : BitVec 8
  measured : BitVec 8
  outcomes : BitVec 8
  deriving DecidableEq, Repr

private def enabled (m g : BitVec 8) : Bool := (m &&& g) == g
private def act (m g : BitVec 8) : BitVec 36 := if enabled m g then 1 else 0
private def bit (s : BitVec 36) (q : Nat) : BitVec 36 := (s >>> q) &&& 1
private def toggle (s : BitVec 36) (q : Nat) (v : BitVec 36) : BitVec 36 :=
  s ^^^ ((v &&& 1) <<< q)
private def clearWire (s : BitVec 36) (q : Nat) : BitVec 36 :=
  s &&& ~~~((1 : BitVec 36) <<< q)
private def setBit (s : BitVec 8) (q : Nat) (v : Bool) : BitVec 8 :=
  if v then s ||| ((1 : BitVec 8) <<< q)
  else s &&& ~~~((1 : BitVec 8) <<< q)

private def tick (m : BitVec 8) (s : State) : Gate → State
  | .x q g => {s with wires := toggle s.wires q (act m g)}
  | .cx a t g => {s with wires := toggle s.wires t (bit s.wires a &&& act m g)}
  | .ccx a b t g => {s with wires := toggle s.wires t (bit s.wires a &&& bit s.wires b &&& act m g)}
  | .swap a b g =>
    let v := (bit s.wires a ^^^ bit s.wires b) &&& act m g
    {s with wires := toggle (toggle s.wires a v) b v}
  | .z q g => {s with phase := Bool.xor s.phase (enabled m g && (bit s.wires q).getLsbD 0)}
  | .cz a b g => {s with phase := Bool.xor s.phase (enabled m g && (bit s.wires a &&& bit s.wires b).getLsbD 0)}
  | .ccz a b c g => {s with phase := Bool.xor s.phase (enabled m g && (bit s.wires a &&& bit s.wires b &&& bit s.wires c).getLsbD 0)}
  | .sign g => {s with phase := Bool.xor s.phase (enabled m g)}
  | .hmr q j => {s with wires := clearWire s.wires q,
                        phase := Bool.xor s.phase (m.getLsbD j && (bit s.wires q).getLsbD 0),
                        measured := setBit s.measured j true,
                        outcomes := setBit s.outcomes j (m.getLsbD j)}
  | .rot q j g => {s with rotations := setBit s.rotations j (enabled m g && (bit s.wires q).getLsbD 0)}

private def run (gs : List Gate) (m : BitVec 8) (s : State) : State :=
  gs.foldl (tick m) s

private def paid : List Gate → Nat
  | [] => 0
  | .ccx _ _ _ _ :: gs | .ccz _ _ _ _ :: gs => 1 + paid gs
  | _ :: gs => paid gs

private def wireOK : Gate → Bool
  | .x q _ | .z q _ => decide (q < 36)
  | .cx a b _ | .swap a b _ | .cz a b _ => decide (a < 36 ∧ b < 36 ∧ a ≠ b)
  | .ccx a b c _ | .ccz a b c _ => decide (a < 36 ∧ b < 36 ∧ c < 36 ∧ a ≠ b ∧ a ≠ c ∧ b ≠ c)
  | .hmr q j | .rot q j _ => decide (q < 36 ∧ j < 8)
  | .sign _ => true

-- Equal-value logical roles may be exchanged without acting on physical data.
def swapRole (s : Fin 37 → Bool) (a b i : Fin 37) : Bool :=
  if i = a then s b else if i = b then s a else s i

theorem equalRoleSwap (s : Fin 37 → Bool) (a b : Fin 37) (h : s a = s b) :
    swapRole s a b = s := by
  funext i
  by_cases hi : i = a
  · subst i
    simp [swapRole, h]
  · by_cases hj : i = b
    · subst i
      simp [swapRole, hi, h]
    · simp [swapRole, hi, hj]

-- Parent slice [9617,9633); classical IDs: 440, 837.
private def old9617 : List Gate := [
  .ccx 29 31 17 0,
  .cx 15 17 0,
  .cx 0 17 0,
  .x 33 0,
  .cz 33 25 2,
  .cz 2 33 2,
  .cz 5 33 2,
  .rot 33 0 0,
  .x 33 0,
  .cz 20 33 2,
  .cz 25 33 2,
  .cz 33 3 2,
  .hmr 33 0,
  .ccx 29 31 33 0]
private def new9617 : List Gate := [
  .cx 15 17 0,
  .cx 0 17 0,
  .x 33 0,
  .cz 33 25 2,
  .cz 2 33 2,
  .cz 5 33 2,
  .rot 33 0 0,
  .x 33 0,
  .cz 20 33 2,
  .cz 25 33 2,
  .cz 33 3 2,
  .hmr 33 0,
  .cx 33 17 0,
  .ccx 29 31 33 0,
  .cx 33 17 0]

theorem local_9617 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old9617 m ⟨x,p,r,h,v⟩ = run new9617 m ⟨x,p,r,h,v⟩ := by
  simp only [old9617, new9617, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_9617 :
    old9617.all wireOK = true ∧ new9617.all wireOK = true ∧
    paid old9617 = 2 ∧ paid new9617 = 1 := by decide

-- Parent slice [13239,13246); classical IDs: 412.
private def old13239 : List Gate := [
  .ccx 30 2 19 0,
  .ccx 34 9 19 0,
  .cx 9 14 0,
  .cx 7 14 0,
  .ccx 30 2 19 0]
private def new13239 : List Gate := [
  .ccx 34 9 19 0,
  .cx 9 14 0,
  .cx 7 14 0]

theorem local_13239 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old13239 m ⟨x,p,r,h,v⟩ = run new13239 m ⟨x,p,r,h,v⟩ := by
  simp only [old13239, new13239, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_13239 :
    old13239.all wireOK = true ∧ new13239.all wireOK = true ∧
    paid old13239 = 3 ∧ paid new13239 = 1 := by decide

-- Parent slice [13419,13443); classical IDs: 403.
private def old13419 : List Gate := [
  .ccx 6 2 4 0,
  .ccx 14 9 4 0,
  .cx 27 4 0,
  .cx 24 4 0,
  .cx 6 4 0,
  .cx 14 4 0,
  .cx 14 4 0,
  .cx 27 4 0,
  .cx 10 0 0,
  .cx 33 0 0,
  .cx 8 0 0,
  .cx 13 0 0,
  .cx 20 0 0,
  .cx 28 0 0,
  .rot 0 0 0,
  .cx 25 0 0,
  .cx 25 4 0,
  .x 0 0,
  .cx 6 14 0,
  .cx 24 14 0,
  .cx 27 14 0,
  .ccx 6 2 14 0]
private def new13419 : List Gate := [
  .ccx 14 9 4 0,
  .cx 27 4 0,
  .cx 24 4 0,
  .cx 6 4 0,
  .cx 14 4 0,
  .cx 14 4 0,
  .cx 27 4 0,
  .cx 10 0 0,
  .cx 33 0 0,
  .cx 8 0 0,
  .cx 13 0 0,
  .cx 20 0 0,
  .cx 28 0 0,
  .rot 0 0 0,
  .cx 25 0 0,
  .cx 25 4 0,
  .x 0 0,
  .cx 6 14 0,
  .cx 24 14 0,
  .cx 27 14 0,
  .cx 14 4 0,
  .ccx 2 6 14 0,
  .cx 14 4 0]

theorem local_13419 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old13419 m ⟨x,p,r,h,v⟩ = run new13419 m ⟨x,p,r,h,v⟩ := by
  simp only [old13419, new13419, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_13419 :
    old13419.all wireOK = true ∧ new13419.all wireOK = true ∧
    paid old13419 = 3 ∧ paid new13419 = 2 := by decide

-- Parent slice [15552,15567); classical IDs: 837.
private def old15552 : List Gate := [
  .ccx 6 32 20 0,
  .ccx 24 28 20 0,
  .x 20 0,
  .cx 9 20 0,
  .cx 16 20 0,
  .cx 17 20 0,
  .cx 32 20 0,
  .cx 0 24 0,
  .cx 9 24 0,
  .cz 29 24 1,
  .cz 26 24 1,
  .cz 25 24 1,
  .ccx 6 32 24 0]
private def new15552 : List Gate := [
  .ccx 24 28 20 0,
  .x 20 0,
  .cx 9 20 0,
  .cx 16 20 0,
  .cx 17 20 0,
  .cx 32 20 0,
  .cx 0 24 0,
  .cx 9 24 0,
  .cz 29 24 1,
  .cz 26 24 1,
  .cz 25 24 1,
  .cx 24 20 0,
  .ccx 6 32 24 0,
  .cx 24 20 0]

theorem local_15552 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old15552 m ⟨x,p,r,h,v⟩ = run new15552 m ⟨x,p,r,h,v⟩ := by
  simp only [old15552, new15552, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_15552 :
    old15552.all wireOK = true ∧ new15552.all wireOK = true ∧
    paid old15552 = 3 ∧ paid new15552 = 2 := by decide

-- Parent slice [16856,16882); classical IDs: 837.
private def old16856 : List Gate := [
  .ccx 27 0 20 0,
  .ccx 22 18 20 0,
  .cx 25 20 0,
  .cx 16 20 0,
  .cx 6 20 0,
  .cx 0 20 0,
  .cx 2 22 0,
  .cz 29 22 1,
  .cz 21 22 1,
  .cz 26 22 1,
  .z 22 1,
  .cz 25 22 1,
  .cz 16 22 1,
  .cz 6 22 1,
  .cz 0 22 1,
  .ccz 27 0 22 1,
  .cz 9 22 1,
  .cz 25 22 1,
  .cz 16 22 1,
  .cz 31 22 1,
  .cz 10 22 1,
  .cz 6 22 1,
  .cz 22 28 1,
  .ccx 27 0 22 0]
private def new16856 : List Gate := [
  .ccx 22 18 20 0,
  .cx 25 20 0,
  .cx 16 20 0,
  .cx 6 20 0,
  .cx 0 20 0,
  .cx 2 22 0,
  .cz 29 22 1,
  .cz 21 22 1,
  .cz 26 22 1,
  .z 22 1,
  .cz 25 22 1,
  .cz 16 22 1,
  .cz 6 22 1,
  .cz 0 22 1,
  .ccz 27 0 22 1,
  .cz 9 22 1,
  .cz 25 22 1,
  .cz 16 22 1,
  .cz 31 22 1,
  .cz 10 22 1,
  .cz 6 22 1,
  .cz 22 28 1,
  .cx 22 20 0,
  .ccx 0 27 22 0,
  .cx 22 20 0]

theorem local_16856 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old16856 m ⟨x,p,r,h,v⟩ = run new16856 m ⟨x,p,r,h,v⟩ := by
  simp only [old16856, new16856, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_16856 :
    old16856.all wireOK = true ∧ new16856.all wireOK = true ∧
    paid old16856 = 4 ∧ paid new16856 = 3 := by decide

-- Parent slice [17319,17333); classical IDs: 837.
private def old17319 : List Gate := [
  .ccx 0 18 25 0,
  .ccx 20 17 25 0,
  .cx 0 25 0,
  .cx 2 20 0,
  .cz 29 20 1,
  .cz 21 20 1,
  .cz 8 20 1,
  .cz 26 20 1,
  .cz 9 20 1,
  .cz 1 20 1,
  .cz 20 24 1,
  .ccx 0 18 20 0]
private def new17319 : List Gate := [
  .ccx 20 17 25 0,
  .cx 0 25 0,
  .cx 2 20 0,
  .cz 29 20 1,
  .cz 21 20 1,
  .cz 8 20 1,
  .cz 26 20 1,
  .cz 9 20 1,
  .cz 1 20 1,
  .cz 20 24 1,
  .cx 20 25 0,
  .ccx 0 18 20 0,
  .cx 20 25 0]

theorem local_17319 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old17319 m ⟨x,p,r,h,v⟩ = run new17319 m ⟨x,p,r,h,v⟩ := by
  simp only [old17319, new17319, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_17319 :
    old17319.all wireOK = true ∧ new17319.all wireOK = true ∧
    paid old17319 = 3 ∧ paid new17319 = 2 := by decide

-- Parent slice [17756,17773); classical IDs: 837.
private def old17756 : List Gate := [
  .ccx 0 17 20 0,
  .ccx 27 34 20 0,
  .cx 0 20 0,
  .cx 2 27 0,
  .cz 29 27 1,
  .cz 26 27 1,
  .z 27 1,
  .cz 0 27 1,
  .ccz 0 27 17 1,
  .cz 10 27 1,
  .cz 25 27 1,
  .cz 14 27 1,
  .z 27 1,
  .cz 27 18 1,
  .ccx 0 17 27 0]
private def new17756 : List Gate := [
  .ccx 27 34 20 0,
  .cx 0 20 0,
  .cx 2 27 0,
  .cz 29 27 1,
  .cz 26 27 1,
  .z 27 1,
  .cz 0 27 1,
  .ccz 0 27 17 1,
  .cz 10 27 1,
  .cz 25 27 1,
  .cz 14 27 1,
  .z 27 1,
  .cz 27 18 1,
  .cx 27 20 0,
  .ccx 0 17 27 0,
  .cx 27 20 0]

theorem local_17756 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old17756 m ⟨x,p,r,h,v⟩ = run new17756 m ⟨x,p,r,h,v⟩ := by
  simp only [old17756, new17756, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_17756 :
    old17756.all wireOK = true ∧ new17756.all wireOK = true ∧
    paid old17756 = 4 ∧ paid new17756 = 3 := by decide

-- Parent slice [18202,18218); classical IDs: 837.
private def old18202 : List Gate := [
  .ccx 20 34 27 0,
  .ccx 0 24 27 0,
  .cx 20 27 0,
  .cx 2 0 0,
  .cz 29 0 1,
  .cz 26 0 1,
  .cz 31 0 1,
  .cz 33 0 1,
  .cz 18 0 1,
  .cz 12 0 1,
  .cz 28 0 1,
  .z 0 1,
  .cz 0 11 1,
  .ccx 20 34 0 0]
private def new18202 : List Gate := [
  .ccx 0 24 27 0,
  .cx 20 27 0,
  .cx 2 0 0,
  .cz 29 0 1,
  .cz 26 0 1,
  .cz 31 0 1,
  .cz 33 0 1,
  .cz 18 0 1,
  .cz 12 0 1,
  .cz 28 0 1,
  .z 0 1,
  .cz 0 11 1,
  .cx 0 27 0,
  .ccx 20 34 0 0,
  .cx 0 27 0]

theorem local_18202 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old18202 m ⟨x,p,r,h,v⟩ = run new18202 m ⟨x,p,r,h,v⟩ := by
  simp only [old18202, new18202, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_18202 :
    old18202.all wireOK = true ∧ new18202.all wireOK = true ∧
    paid old18202 = 3 ∧ paid new18202 = 2 := by decide

-- Parent slice [18624,18645); classical IDs: 837.
private def old18624 : List Gate := [
  .ccx 27 24 0 0,
  .ccx 20 6 0 0,
  .cx 27 0 0,
  .cx 2 20 0,
  .cz 29 20 1,
  .cz 21 20 1,
  .cz 8 20 1,
  .cz 26 20 1,
  .cz 9 20 1,
  .cz 18 20 1,
  .cz 12 20 1,
  .cz 17 20 1,
  .cz 28 20 1,
  .cz 14 20 1,
  .z 20 1,
  .cz 20 25 1,
  .cz 20 5 1,
  .cz 20 34 1,
  .ccx 27 24 20 0]
private def new18624 : List Gate := [
  .ccx 20 6 0 0,
  .cx 27 0 0,
  .cx 2 20 0,
  .cz 29 20 1,
  .cz 21 20 1,
  .cz 8 20 1,
  .cz 26 20 1,
  .cz 9 20 1,
  .cz 18 20 1,
  .cz 12 20 1,
  .cz 17 20 1,
  .cz 28 20 1,
  .cz 14 20 1,
  .z 20 1,
  .cz 20 25 1,
  .cz 20 5 1,
  .cz 20 34 1,
  .cx 20 0 0,
  .ccx 24 27 20 0,
  .cx 20 0 0]

theorem local_18624 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old18624 m ⟨x,p,r,h,v⟩ = run new18624 m ⟨x,p,r,h,v⟩ := by
  simp only [old18624, new18624, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_18624 :
    old18624.all wireOK = true ∧ new18624.all wireOK = true ∧
    paid old18624 = 3 ∧ paid new18624 = 2 := by decide

-- Parent slice [19030,19050); classical IDs: 837.
private def old19030 : List Gate := [
  .ccx 0 6 20 0,
  .ccx 27 30 20 0,
  .cx 0 20 0,
  .cx 2 27 0,
  .cz 29 27 1,
  .cz 21 27 1,
  .cz 8 27 1,
  .cz 26 27 1,
  .cz 31 27 1,
  .cz 23 27 1,
  .cz 17 27 1,
  .cz 28 27 1,
  .cz 14 27 1,
  .cz 34 27 1,
  .cz 2 27 1,
  .cz 27 11 1,
  .cz 27 24 1,
  .ccx 0 6 27 0]
private def new19030 : List Gate := [
  .ccx 27 30 20 0,
  .cx 0 20 0,
  .cx 2 27 0,
  .cz 29 27 1,
  .cz 21 27 1,
  .cz 8 27 1,
  .cz 26 27 1,
  .cz 31 27 1,
  .cz 23 27 1,
  .cz 17 27 1,
  .cz 28 27 1,
  .cz 14 27 1,
  .cz 34 27 1,
  .cz 2 27 1,
  .cz 27 11 1,
  .cz 27 24 1,
  .cx 27 20 0,
  .ccx 0 6 27 0,
  .cx 27 20 0]

theorem local_19030 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old19030 m ⟨x,p,r,h,v⟩ = run new19030 m ⟨x,p,r,h,v⟩ := by
  simp only [old19030, new19030, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_19030 :
    old19030.all wireOK = true ∧ new19030.all wireOK = true ∧
    paid old19030 = 3 ∧ paid new19030 = 2 := by decide

-- Parent slice [30503,30553); classical IDs: 1, 806, 808.
private def old30503 : List Gate := [
  .ccx 5 19 20 0,
  .cx 34 20 0,
  .cx 33 20 0,
  .cx 17 20 0,
  .cz 17 6 2,
  .cz 35 6 2,
  .cz 33 6 2,
  .cz 28 6 2,
  .cz 8 6 2,
  .cz 9 6 2,
  .cz 18 6 2,
  .cz 11 6 2,
  .cz 0 6 2,
  .cz 13 6 2,
  .cz 4 6 2,
  .cz 5 6 2,
  .cz 15 6 2,
  .cz 6 1 2,
  .cz 17 6 4,
  .cz 35 6 4,
  .cz 33 6 4,
  .cz 28 6 4,
  .cz 8 6 4,
  .cz 9 6 4,
  .cz 18 6 4,
  .cz 11 6 4,
  .cz 0 6 4,
  .cz 13 6 4,
  .cz 4 6 4,
  .cz 5 6 4,
  .cz 15 6 4,
  .cz 6 1 4,
  .cx 2 23 0,
  .swap 23 2 2,
  .swap 23 2 4,
  .swap 23 2 6,
  .hmr 23 0,
  .ccx 5 19 23 0]
private def new30503 : List Gate := [
  .cx 34 20 0,
  .cx 33 20 0,
  .cx 17 20 0,
  .cz 17 6 2,
  .cz 35 6 2,
  .cz 33 6 2,
  .cz 28 6 2,
  .cz 8 6 2,
  .cz 9 6 2,
  .cz 18 6 2,
  .cz 11 6 2,
  .cz 0 6 2,
  .cz 13 6 2,
  .cz 4 6 2,
  .cz 5 6 2,
  .cz 15 6 2,
  .cz 6 1 2,
  .cz 17 6 4,
  .cz 35 6 4,
  .cz 33 6 4,
  .cz 28 6 4,
  .cz 8 6 4,
  .cz 9 6 4,
  .cz 18 6 4,
  .cz 11 6 4,
  .cz 0 6 4,
  .cz 13 6 4,
  .cz 4 6 4,
  .cz 5 6 4,
  .cz 15 6 4,
  .cz 6 1 4,
  .cx 2 23 0,
  .swap 23 2 2,
  .swap 23 2 4,
  .swap 23 2 6,
  .hmr 23 0,
  .cx 23 20 0,
  .ccx 5 19 23 0,
  .cx 23 20 0]

theorem local_30503 (x : BitVec 36) (m : BitVec 8) (p : Bool) (r h v : BitVec 8) :
    run old30503 m ⟨x,p,r,h,v⟩ = run new30503 m ⟨x,p,r,h,v⟩ := by
  simp only [old30503, new30503, run, List.foldl_cons, List.foldl_nil, tick,
    enabled, act, bit, toggle, clearWire, setBit, State.mk.injEq]
  bv_decide

theorem resource_30503 :
    old30503.all wireOK = true ∧ new30503.all wireOK = true ∧
    paid old30503 = 2 ∧ paid new30503 = 1 := by decide

theorem totalPaid :
    (paid old9617 + paid old13239 + paid old13419 + paid old15552 + paid old16856 + paid old17319 + paid old17756 + paid old18202 + paid old18624 + paid old19030 + paid old30503) = 33 ∧
    (paid new9617 + paid new13239 + paid new13419 + paid new15552 + paid new16856 + paid new17319 + paid new17756 + paid new18202 + paid new18624 + paid new19030 + paid new30503) = 21 := by decide

end GVQCC.CommutingHubV8
