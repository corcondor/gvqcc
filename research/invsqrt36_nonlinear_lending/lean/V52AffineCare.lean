import Std.Tactic
namespace GVQCC.V52

def x (a b : Bool) : Bool := Bool.xor a b

theorem affine_three (a b c s : Bool) (ha : a = s)
    (hb : b = s) (hc : c = s) :
    x (x a b) c = s := by
  subst a
  subst b
  subst c
  cases s <;> decide

theorem linear_shift (a b c d : Bool) :
    x (x a b) (x c d) = x (x a c) (x b d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem common_factor (a b c d : Bool) :
    x (a && b && c) (a && b && d) = (a && b && x c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem dirty_restore (r p : Bool) : x (x r p) p = r := by
  cases r <;> cases p <;> decide

theorem dirty_apply (t r p s : Bool) :
    x (x t (r && s)) (x r p && s) = x t (p && s) := by
  cases t <;> cases r <;> cases p <;> cases s <;> decide

-- An affine flat is represented as H translated by a. Adding direction d
-- enlarges its support to exactly the union of H and the shifted H.
def safe {A : Type} (F H : A → Prop) : Prop :=
  ∀ a, H a → ¬ F a

theorem union_safe {A : Type} (F H J : A → Prop) :
    safe F (fun a => H a ∨ J a) ↔ safe F H ∧ safe F J := by
  constructor
  · intro h
    exact ⟨fun a ha => h a (Or.inl ha), fun a ha => h a (Or.inr ha)⟩
  · intro h a ha
    cases ha with
    | inl hh => exact h.1 a hh
    | inr hj => exact h.2 a hj

-- In a quotient, all rows in the same coset have the same image.
-- A coset avoiding forbidden images contains no forbidden source row.
theorem quotient_safe {A B : Type} (q : A → B) (bad : A → Prop) (b : B)
    (h : ¬ ∃ a, bad a ∧ q a = b) :
    ∀ a, q a = b → ¬ bad a := by
  intro a ha hb
  exact h ⟨a,hb,ha⟩

def z (b : Bool) : Int := if b then 1 else 0

-- A shared selector can correct a whole weighted phase pattern, without
-- requiring each term individually to satisfy the final error inequality.
theorem phase_toggle (f s : Bool) (a : Int) :
    a * z (x f s) = a * z f + z s * (a * (1 - 2 * z f)) := by
  cases f <;> cases s <;> simp [z,x,Bool.xor] <;> omega

theorem two_phase_toggle (f g s : Bool) (a b : Int) :
    a * z (x f s) + b * z (x g s) =
      a * z f + b * z g +
      z s * (a * (1 - 2 * z f) + b * (1 - 2 * z g)) := by
  cases f <;> cases g <;> cases s <;> simp [z,x,Bool.xor] <;> omega

theorem polarized_transport (a b da db : Bool) :
    x (x a da && x b db) (a && b) =
      x (x (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

def abelL (c : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (m,d) :: xs => x (m && x c d) (abelL d xs)
def abelR (p c : Bool) : List (Bool × Bool) → Bool
  | [] => p && c
  | (m,d) :: xs => x (x p m && c) (abelR m d xs)
theorem abel_step (p c m d v : Bool) :
    x (p && c) (x (m && x c d) v) =
    x (x p m && c) (x (m && d) v) := by
  cases p <;> cases c <;> cases m <;> cases d <;> cases v <;> decide
theorem abel_multi (xs : List (Bool × Bool)) (p c : Bool) :
    x (p && c) (abelL c xs) = abelR p c xs := by
  induction xs generalizing p c with
  | nil => cases p <;> cases c <;> rfl
  | cons hd tl ih =>
    rcases hd with ⟨m,d⟩
    simp only [abelL, abelR]
    rw [← ih m d]
    exact abel_step p c m d (abelL d tl)

theorem resource_accounting :
    45297 - 6729 = 38568 ∧ 6729 - 1489 = 5240 ∧
    107384 - 65848 = 41536 ∧
    192 - 119 = 73 ∧ 27 - 1 = 26 := by decide

end GVQCC.V52
