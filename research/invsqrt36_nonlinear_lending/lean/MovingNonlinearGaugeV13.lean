import Std.Tactic.BVDecide

/- Actual V13 gate lists from pinned PR59 wide KMB. Five erased events
   are normalized to zero ONLY for the local lemma; independent
   whole-domain BDD transcript cancellation discharges their physical
   removal. The deferred event case proves arbitrary outcomes and their
   classical record identities, without normalizing either outcome.
   q36 is zero at entry; all other basis bits are arbitrary. -/
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.MovingNonlinearGaugeV13
inductive Gate where
  | x (q : Nat)
  | cx (a t : Nat)
  | swap (a b : Nat)
  | ccx (a b t : Nat)
  | z (q g : Nat)
  | cz (a b g : Nat)
  | ccz (a b c g : Nat)
  | sign (g : Nat)
  | hmr (q e : Nat)
  | storeZero (e : Nat)
  deriving DecidableEq, Repr
structure State where
  wires : BitVec 37
  phase : Bool
  r0 : Bool
  r1 : Bool
  deriving DecidableEq, Repr
def bit (s : BitVec 37) (q : Nat) : BitVec 37 := (s >>> q) &&& 1
def toggle (s : BitVec 37) (q : Nat) (v : BitVec 37) := s ^^^ (v <<< q)
def clearWire (s : BitVec 37) (q : Nat) := s &&& ~~~((1 : BitVec 37) <<< q)
def enabled (g : Bool) (s : State) (k : Nat) : Bool :=
  if k == 0 then g else if k == 1 then s.r0 else true
def store (s : State) (k : Nat) (m : Bool) : State :=
  if k == 0 then {s with r0 := m} else {s with r1 := m}
def step (g m0 m1 : Bool) (s : State) : Gate → State
  | .x q => {s with wires := toggle s.wires q 1}
  | .cx a t => {s with wires := toggle s.wires t (bit s.wires a)}
  | .ccx a b t => {s with wires := toggle s.wires t (bit s.wires a &&& bit s.wires b)}
  | .swap a b =>
    let v := bit s.wires a ^^^ bit s.wires b
    {s with wires := toggle (toggle s.wires a v) b v}
  | .z a k => {s with phase := Bool.xor s.phase (enabled g s k && (bit s.wires a).getLsbD 0)}
  | .cz a b k => {s with phase := Bool.xor s.phase (enabled g s k && (bit s.wires a &&& bit s.wires b).getLsbD 0)}
  | .ccz a b c k => {s with phase := Bool.xor s.phase (enabled g s k && (bit s.wires a &&& bit s.wires b &&& bit s.wires c).getLsbD 0)}
  | .sign k => {s with phase := Bool.xor s.phase (enabled g s k)}
  | .hmr q k =>
    let m := if k == 0 then m0 else m1
    store {s with wires := clearWire s.wires q, phase := Bool.xor s.phase (m && (bit s.wires q).getLsbD 0)} k m
  | .storeZero k => store s k false
def run (gs : List Gate) (g m0 m1 : Bool) (s : State) := gs.foldl (step g m0 m1) s
def paid (gs : List Gate) : Nat := (gs.filter fun g => match g with | .ccx _ _ _ | .ccz _ _ _ _ => true | _ => false).length
def measurements (gs : List Gate) : Nat := (gs.filter fun g => match g with | .hmr _ _ => true | _ => false).length
def wireOK (n : Nat) : Gate → Bool
  | .x a | .z a _ | .hmr a _ => decide (a < n)
  | .cx a b | .swap a b | .cz a b _ => decide (a < n ∧ b < n ∧ a ≠ b)
  | .ccx a b c | .ccz a b c _ => decide (a < n ∧ b < n ∧ c < n ∧ a ≠ b ∧ b ≠ c ∧ a ≠ c)
  | .sign _ | .storeZero _ => true

def f (a b : Bool) := Bool.xor a (a && b)
theorem borrowedInvolution (a b c : Bool) :
    Bool.xor (Bool.xor c (f a b)) (f a b) = c := by
  unfold f
  bv_decide
theorem affineGaugeTransport (x y h u v : Bool) :
    Bool.xor (Bool.xor y (v && h)) (Bool.xor x (u && h)) =
    Bool.xor (Bool.xor y x) (Bool.xor u v && h) := by bv_decide
theorem quadraticPhasePullback (x y h u v : Bool) :
    Bool.xor ((Bool.xor x (u && h)) && (Bool.xor y (v && h))) (x && y) =
    (h && Bool.xor (Bool.xor (u && y) (v && x)) (u && v)) := by bv_decide
def old_25112 : List Gate := [.swap 30 36, .ccx 25 29 30, .cx 25 30, .cx 3 30, .cx 34 11, .cx 34 10, .cx 34 8, .cx 34 2, .cx 29 2, .cx 25 2, .cx 15 8, .cx 10 8, .cx 10 11, .swap 10 11, .cx 14 8, .swap 11 8, .cx 3 2, .cz 0 30 0, .cz 4 30 0, .cz 6 30 0, .cz 13 30 0, .cz 22 30 0, .cz 28 30 0, .cz 30 31 0, .cz 0 34 0, .cz 4 34 0, .cz 6 34 0, .cz 13 34 0, .cz 22 34 0, .cz 28 34 0, .cz 31 34 0, .cx 2 8, .x 2, .ccx 30 2 34, .cx 30 2, .hmr 30 0, .swap 30 36]
def new_25112 : List Gate := [.cx 34 11, .cx 34 10, .cx 34 8, .cx 34 2, .cx 29 2, .cx 25 2, .cx 15 8, .cx 10 8, .cx 10 11, .swap 10 11, .cx 14 8, .swap 11 8, .cx 3 2, .cx 25 3, .ccx 25 29 3, .cz 0 3 0, .cz 3 4 0, .cz 3 6 0, .cz 3 13 0, .cz 3 22 0, .cz 3 28 0, .cz 3 31 0, .cz 0 34 0, .cz 4 34 0, .cz 6 34 0, .cz 13 34 0, .cz 22 34 0, .cz 28 34 0, .cz 31 34 0, .cx 2 8, .x 2, .ccx 3 2 34, .cx 3 2, .ccx 25 29 3, .cx 25 3, .storeZero 0]
theorem eq_25112 (s : BitVec 37) (p g m0 m1 r0 r1 : Bool) :
    run old_25112 g false m1 ⟨clearWire s 36,p,r0,r1⟩ =
    run new_25112 g false m1 ⟨clearWire s 36,p,r0,r1⟩ := by
  simp only [old_25112, new_25112, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, store, State.mk.injEq]
  bv_decide
theorem res_25112 :
    old_25112.all (wireOK 37) = true ∧ new_25112.all (wireOK 36) = true ∧
    paid old_25112 = 2 ∧ paid new_25112 = 3 ∧
    old_25112.length = 37 ∧ new_25112.length = 36 ∧
    measurements old_25112 = 1 ∧ measurements new_25112 = 0 := by decide

def old_26189 : List Gate := [.swap 29 36, .ccx 16 30 29, .cx 16 29, .cx 3 29, .cx 34 5, .cx 34 2, .cx 30 2, .cx 16 2, .cx 15 5, .cx 9 5, .cx 8 5, .cx 3 2, .cx 2 5, .cz 0 29 0, .cz 1 29 0, .cz 3 29 0, .cz 4 29 0, .cz 9 29 0, .cz 13 29 0, .cz 22 29 0, .cz 24 29 0, .cz 25 29 0, .cz 28 29 0, .cz 0 34 0, .cz 1 34 0, .cz 3 34 0, .cz 4 34 0, .cz 9 34 0, .cz 13 34 0, .cz 22 34 0, .cz 24 34 0, .cz 25 34 0, .cz 28 34 0, .x 2, .ccx 29 2 34, .cx 29 2, .hmr 29 0, .swap 29 36]
def new_26189 : List Gate := [.cx 34 5, .cx 34 2, .cx 30 2, .cx 16 2, .cx 15 5, .cx 9 5, .cx 8 5, .cx 3 2, .cx 3 0, .cx 16 3, .ccx 16 30 3, .cx 3 0, .cx 2 5, .z 3 0, .cz 0 3 0, .cz 1 3 0, .cz 3 4 0, .cz 3 9 0, .cz 3 13 0, .cz 3 22 0, .cz 3 24 0, .cz 3 25 0, .cz 3 28 0, .cz 0 34 0, .cz 1 34 0, .cz 3 34 0, .cz 4 34 0, .cz 9 34 0, .cz 13 34 0, .cz 22 34 0, .cz 24 34 0, .cz 25 34 0, .cz 28 34 0, .x 2, .ccx 3 2 34, .cx 3 2, .cx 3 0, .cx 16 3, .ccx 16 30 3, .cx 3 0, .storeZero 0]
theorem eq_26189 (s : BitVec 37) (p g m0 m1 r0 r1 : Bool) :
    run old_26189 g false m1 ⟨clearWire s 36,p,r0,r1⟩ =
    run new_26189 g false m1 ⟨clearWire s 36,p,r0,r1⟩ := by
  simp only [old_26189, new_26189, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, store, State.mk.injEq]
  bv_decide
theorem res_26189 :
    old_26189.all (wireOK 37) = true ∧ new_26189.all (wireOK 36) = true ∧
    paid old_26189 = 2 ∧ paid new_26189 = 3 ∧
    old_26189.length = 38 ∧ new_26189.length = 41 ∧
    measurements old_26189 = 1 ∧ measurements new_26189 = 0 := by decide

def old_27227 : List Gate := [.swap 26 36, .ccx 16 29 26, .cx 16 26, .cx 3 26, .cx 19 10, .cx 19 20, .cx 34 19, .cx 34 2, .cx 29 2, .cx 16 2, .cx 15 20, .z 26 0, .cz 2 26 0, .cz 6 26 0, .cz 22 26 0, .cz 26 28 0, .cz 3 34 0, .cz 6 34 0, .cz 22 34 0, .cz 28 34 0, .cx 15 19, .cx 13 19, .cx 9 20, .cx 9 19, .cx 3 2, .cx 2 19, .x 2, .ccx 26 2 34, .cx 26 2, .hmr 26 0, .swap 26 36]
def new_27227 : List Gate := [.cx 3 2, .cx 3 6, .cx 16 3, .ccx 16 29 3, .cx 3 6, .cx 3 2, .cx 19 10, .cx 19 20, .cx 34 19, .cx 34 2, .cx 29 2, .cx 16 2, .cx 15 20, .z 3 0, .cz 2 3 0, .cz 3 6 0, .cz 3 22 0, .cz 3 28 0, .cz 3 34 0, .cz 6 34 0, .cz 22 34 0, .cz 28 34 0, .cx 15 19, .cx 13 19, .cx 9 20, .cx 9 19, .cx 3 2, .cx 2 19, .x 2, .ccx 3 2 34, .cx 3 2, .cx 3 6, .cx 16 3, .ccx 16 29 3, .cx 3 6, .storeZero 0]
theorem eq_27227 (s : BitVec 37) (p g m0 m1 r0 r1 : Bool) :
    run old_27227 g false m1 ⟨clearWire s 36,p,r0,r1⟩ =
    run new_27227 g false m1 ⟨clearWire s 36,p,r0,r1⟩ := by
  simp only [old_27227, new_27227, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, store, State.mk.injEq]
  bv_decide
theorem res_27227 :
    old_27227.all (wireOK 37) = true ∧ new_27227.all (wireOK 36) = true ∧
    paid old_27227 = 2 ∧ paid new_27227 = 3 ∧
    old_27227.length = 31 ∧ new_27227.length = 36 ∧
    measurements old_27227 = 1 ∧ measurements new_27227 = 0 := by decide

def old_27754 : List Gate := [.swap 26 36, .ccx 20 29 26, .cx 20 26, .cx 3 26, .cx 34 13, .cx 34 2, .cx 29 2, .cx 21 13, .cx 20 2, .cx 19 13, .cx 15 13, .cx 3 2, .cx 2 13, .cz 2 26 0, .cz 12 26 0, .cz 25 26 0, .cz 12 34 0, .cz 25 34 0, .x 2, .ccx 26 2 34, .cx 26 2, .hmr 26 0, .swap 26 36]
def new_27754 : List Gate := [.cx 34 13, .cx 34 2, .cx 29 2, .cx 21 13, .cx 20 2, .cx 19 13, .cx 15 13, .cx 3 2, .cx 2 13, .cx 20 3, .ccx 20 29 3, .cz 2 3 0, .cz 3 12 0, .cz 3 25 0, .cz 12 34 0, .cz 25 34 0, .x 2, .ccx 3 2 34, .cx 3 2, .ccx 20 29 3, .cx 20 3, .storeZero 0]
theorem eq_27754 (s : BitVec 37) (p g m0 m1 r0 r1 : Bool) :
    run old_27754 g false m1 ⟨clearWire s 36,p,r0,r1⟩ =
    run new_27754 g false m1 ⟨clearWire s 36,p,r0,r1⟩ := by
  simp only [old_27754, new_27754, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, store, State.mk.injEq]
  bv_decide
theorem res_27754 :
    old_27754.all (wireOK 37) = true ∧ new_27754.all (wireOK 36) = true ∧
    paid old_27754 = 2 ∧ paid new_27754 = 3 ∧
    old_27754.length = 23 ∧ new_27754.length = 22 ∧
    measurements old_27754 = 1 ∧ measurements new_27754 = 0 := by decide

def old_21386 : List Gate := [.swap 2 36, .ccx 3 29 2, .cx 2 30, .cx 34 6, .cx 15 6, .cx 12 6, .cx 7 6, .cx 5 6, .ccx 30 6 34, .cx 30 6, .cx 2 30, .hmr 2 0, .swap 2 36, .cz 3 29 1, .cx 30 3, .cx 29 3, .cx 3 29, .cx 22 29, .hmr 22 1]
def new_21386 : List Gate := [.ccx 3 29 30, .cx 34 6, .cx 15 6, .cx 12 6, .cx 7 6, .cx 5 6, .ccx 30 6 34, .cx 30 6, .ccx 3 29 30, .cx 30 3, .cx 29 3, .cx 3 29, .cx 22 29, .hmr 22 1, .hmr 22 0]
theorem eq_21386 (s : BitVec 37) (p g m0 m1 r0 r1 : Bool) :
    run old_21386 g m0 m1 ⟨clearWire s 36,p,r0,r1⟩ =
    run new_21386 g m0 m1 ⟨clearWire s 36,p,r0,r1⟩ := by
  simp only [old_21386, new_21386, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, store, State.mk.injEq]
  bv_decide
theorem res_21386 :
    old_21386.all (wireOK 37) = true ∧ new_21386.all (wireOK 36) = true ∧
    paid old_21386 = 2 ∧ paid new_21386 = 3 ∧
    old_21386.length = 19 ∧ new_21386.length = 15 ∧
    measurements old_21386 = 2 ∧ measurements new_21386 = 2 := by decide

def old_28272 : List Gate := [.swap 26 36, .ccx 27 29 26, .cx 26 27, .cx 3 27, .cx 34 16, .cx 34 2, .cx 29 2, .cx 27 2, .cx 26 2, .cx 19 16, .cx 2 16, .x 2, .cz 3 34 0, .cz 12 34 0, .cz 2 27 0, .cz 3 27 0, .cz 12 27 0, .ccx 27 2 34, .cx 27 26, .cx 27 2, .hmr 27 0, .swap 27 36]
def new_28272 : List Gate := [.cx 34 16, .cx 34 2, .cx 29 2, .cx 27 2, .cx 3 2, .cx 3 12, .cx 27 3, .ccx 27 29 3, .cx 3 12, .cx 19 16, .cx 2 16, .x 2, .z 3 0, .cz 2 3 0, .cz 3 12 0, .cz 3 34 0, .cz 12 34 0, .ccx 3 2 34, .cx 3 2, .cx 3 12, .cx 27 3, .ccx 27 29 3, .cx 3 12, .cx 3 27, .swap 27 26, .storeZero 0]
theorem eq_28272 (s : BitVec 37) (p g m0 m1 r0 r1 : Bool) :
    run old_28272 g false m1 ⟨clearWire s 36,p,r0,r1⟩ =
    run new_28272 g false m1 ⟨clearWire s 36,p,r0,r1⟩ := by
  simp only [old_28272, new_28272, run, List.foldl_cons, List.foldl_nil, step, bit, toggle, clearWire, enabled, store, State.mk.injEq]
  bv_decide
theorem res_28272 :
    old_28272.all (wireOK 37) = true ∧ new_28272.all (wireOK 36) = true ∧
    paid old_28272 = 2 ∧ paid new_28272 = 3 ∧
    old_28272.length = 22 ∧ new_28272.length = 26 ∧
    measurements old_28272 = 1 ∧ measurements new_28272 = 0 := by decide

end GVQCC.MovingNonlinearGaugeV13
