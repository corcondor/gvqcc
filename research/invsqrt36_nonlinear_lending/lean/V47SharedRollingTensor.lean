import Std.Tactic
namespace GVQCC.V47
def x (a b : Bool) : Bool := Bool.xor a b
def parity : List Bool → Bool
  | [] => false
  | a :: as => x a (parity as)
theorem shared_pair (a b c d : Bool) :
    x (a && b && c) (a && b && d) = (a && b && x c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
theorem dirty_hub (t r s p : Bool) :
    x (x t (s && r)) (s && x r p) = x t (s && p) := by
  cases t <;> cases r <;> cases s <;> cases p <;> decide
theorem dirty_hub_restore (r p : Bool) : x (x r p) p = r := by
  cases r <;> cases p <;> decide
theorem distributed_hub (s : Bool) (ps : List Bool) :
    parity (ps.map (fun p => s && p)) = (s && parity ps) := by
  induction ps with
  | nil => cases s <;> rfl
  | cons p ps ih =>
    simp only [List.map_cons, parity, ih]
    cases s <;> cases p <;> cases h : parity ps <;> decide
theorem deferred_measurement (m before after : Bool) (h : before = after) :
    x (m && before) (m && after) = false := by
  subst after
  cases m <;> cases before <;> decide
theorem polarized_transport (a b da db : Bool) :
    x (x a da && x b db) (a && b) =
      x (x (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
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
theorem complement_mask (v f : Bool) :
    (v && !f) = x v (v && f) := by
  cases v <;> cases f <;> decide
theorem cost_accounting : 214 - 97 = 117 ∧ 686 - 251 = 435 ∧
    113257 - 48934 = 64323 ∧ 291 - 251 = 40 := by decide
end GVQCC.V47
