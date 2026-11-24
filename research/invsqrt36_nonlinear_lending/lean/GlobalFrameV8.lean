import Std.Tactic.BVDecide

namespace GlobalFrameV8
inductive G where
  | sw (a b : Nat)
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  | zif (q c : Nat)
  | cz (a b : Nat)
  | beginIf (c : Nat)
  | endIf
  | hmr (q c : Nat)
  deriving DecidableEq

structure St where
  q : Nat → Bool
  c : Nat → Bool
  phase : Bool
  active : Bool
  scopes : List Bool

def put (f : Nat → Bool) (i : Nat) (v : Bool) : Nat → Bool :=
  fun j => if j = i then v else f j

def step (m : Bool) (s : St) (g : G) : St :=
  match g with
  | .sw a b =>
      { s with q := put (put s.q a (if s.active then s.q b else s.q a)) b (if s.active then s.q a else s.q b) }
  | .cx a t => { s with q := put s.q t (Bool.xor (s.q t) (s.active && s.q a)) }
  | .ccx a b t => { s with q := put s.q t (Bool.xor (s.q t) (s.active && s.q a && s.q b)) }
  | .zif q c => { s with phase := Bool.xor s.phase (s.active && s.c c && s.q q) }
  | .cz a b => { s with phase := Bool.xor s.phase (s.active && s.q a && s.q b) }
  | .beginIf c => { s with active := s.active && s.c c, scopes := s.active :: s.scopes }
  | .endIf => { s with active := s.scopes.headD false, scopes := s.scopes.tail }
  | .hmr q c => { s with q := put s.q q (if s.active then false else s.q q),
                          c := put s.c c (if s.active then m else s.c c),
                          phase := Bool.xor s.phase (s.active && s.q q && m) }

def run (m : Bool) (s : St) (gs : List G) : St := gs.foldl (step m) s

-- Actual graft KMB [24827,24839), frame KMB [22383,22393).
def oldList : List G := [.sw 27 36, .ccx 29 30 27, .cx 27 29, .cx 22 29,
  .zif 29 302, .cx 29 27, .beginIf 837, .cz 12 27, .cz 25 27, .endIf,
  .hmr 27 481, .sw 27 36]
def newList : List G := [.ccx 29 30 36, .cx 36 29, .cx 22 29,
  .zif 29 302, .cx 29 36, .beginIf 837, .cz 12 36, .cz 25 36, .endIf,
  .hmr 36 481]

def start (q c : Nat → Bool) (p : Bool) : St := ⟨q,c,p,true,[]⟩
def paid (g : G) : Bool := match g with | .ccx _ _ _ => true | _ => false

theorem actual_resources : oldList.length = 12 ∧ newList.length = 10 ∧
    (oldList.filter paid).length = 1 ∧ (newList.filter paid).length = 1 := by decide

-- Arbitrary incident state, classical guards, phase, and independent HMR outcome.
theorem actual_phase_classical (q c : Nat → Bool) (p m : Bool) :
    (run m (start q c p) oldList).phase = (run m (start q c p) newList).phase ∧
    (run m (start q c p) oldList).c = (run m (start q c p) newList).c ∧
    (run m (start q c p) oldList).active = (run m (start q c p) newList).active ∧
    (run m (start q c p) oldList).scopes = (run m (start q c p) newList).scopes := by
  simp [run, start, oldList, newList, step, put, List.foldl]

theorem actual_state (q c : Nat → Bool) (p m : Bool) :
    (run m (start q c p) oldList).q = (run m (start q c p) newList).q := by
  funext i
  by_cases h27 : i = 27
  · subst i; simp [run, start, oldList, newList, step, put, List.foldl]
  by_cases h29 : i = 29
  · subst i; simp [run, start, oldList, newList, step, put, List.foldl]
  by_cases h36 : i = 36
  · subst i; simp [run, start, oldList, newList, step, put, List.foldl]
  · simp [run, start, oldList, newList, step, put, List.foldl, h27, h29, h36]

end GlobalFrameV8
