import Std.Tactic
namespace GVQCC.V38

def x (a b : Bool) : Bool := Bool.xor a b

theorem borrowed_cubic (a b c r : Bool) :
    x ((x r (a && b)) && c) (r && c) = (a && b && c) := by
  cases a <;> cases b <;> cases c <;> cases r <;> decide

theorem borrowed_restore (r a b : Bool) : x (x r (a && b)) (a && b) = r := by
  cases r <;> cases a <;> cases b <;> decide

def bridgeOld (a p y z h : Bool) : Bool :=
  let f := a && p
  x (x (x (x (x (x p h) z) y) true) f) ((x (x p y) f) && !(x y z))
def bridgeNew (a p y z h : Bool) : Bool :=
  x (x (x h z) true) ((x y z) && (x y ((!a) && p)))
theorem bridge_fused (a p y z h : Bool) : bridgeOld a p y z h = bridgeNew a p y z h := by
  cases a <;> cases p <;> cases y <;> cases z <;> cases h <;> decide

def maj (a b c : Bool) : Bool := x a (x b a && x c a)
def forwardC (a b c : Bool) : Bool × Bool × Bool :=
  (x a c, x b c, x c (x a c && x b c))
def reverseC (a b v : Bool) : Bool × Bool × Bool :=
  let c := x v (a && b)
  let a0 := x a c
  (a0, x a0 b, c)
theorem c_target_maj (a b c : Bool) : (forwardC a b c).2.2 = maj a b c := by
  cases a <;> cases b <;> cases c <;> decide
theorem c_target_uma (a b c : Bool) :
    reverseC (forwardC a b c).1 (forwardC a b c).2.1 (forwardC a b c).2.2 =
      (a, x (x a b) c, c) := by
  cases a <;> cases b <;> cases c <;> decide

def forwardB (a b c : Bool) : Bool × Bool × Bool :=
  (x a b, x b (x a b && x c b), x c b)
def reverseB (a v c : Bool) : Bool × Bool × Bool :=
  let b := x v (a && c)
  let a0 := x a b
  let c0 := x c b
  (a0, x (x b a0) c0, c0)
theorem b_target_maj (a b c : Bool) : (forwardB a b c).2.1 = maj a b c := by
  cases a <;> cases b <;> cases c <;> decide
theorem b_target_uma (a b c : Bool) :
    reverseB (forwardB a b c).1 (forwardB a b c).2.1 (forwardB a b c).2.2 =
      (a, x (x a b) c, c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem common_factor_fuse (a b c t : Bool) :
    x (x t (a && b)) (a && c) = x t (a && x b c) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem anf_split (m low high : Bool) :
    (if m then high else low) = x low (m && x low high) := by
  cases m <;> cases low <;> cases high <;> decide

def phaseL (c : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (m,d) :: xs => x (m && x c d) (phaseL d xs)
def phaseR (p c : Bool) : List (Bool × Bool) → Bool
  | [] => p && c
  | (m,d) :: xs => x (x p m && c) (phaseR m d xs)
theorem abel_step (p c m d z : Bool) :
    x (p && c) (x (m && x c d) z) =
      x (x p m && c) (x (m && d) z) := by
  cases p <;> cases c <;> cases m <;> cases d <;> cases z <;> decide
theorem abel_multistage (xs : List (Bool × Bool)) (p c : Bool) :
    x (p && c) (phaseL c xs) = phaseR p c xs := by
  induction xs generalizing p c with
  | nil => cases p <;> cases c <;> rfl
  | cons hd tl ih =>
    rcases hd with ⟨m,d⟩
    simp only [phaseL, phaseR]
    rw [← ih m d]
    exact abel_step p c m d (phaseL d tl)

end GVQCC.V38
