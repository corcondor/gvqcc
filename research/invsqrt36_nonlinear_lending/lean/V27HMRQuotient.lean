import Std.Tactic
namespace GVQCC.V27

def parity : List Bool → Bool
  | [] => false
  | a :: xs => Bool.xor a (parity xs)

theorem parity_append (xs ys : List Bool) :
    parity (xs ++ ys) = Bool.xor (parity xs) (parity ys) := by
  induction xs with
  | nil =>
    change parity ys = Bool.xor false (parity ys)
    cases parity ys <;> rfl
  | cons a xs ih =>
    change Bool.xor a (parity (xs ++ ys)) =
      Bool.xor (Bool.xor a (parity xs)) (parity ys)
    rw [ih]
    cases a <;> cases parity xs <;> cases parity ys <;> rfl

theorem split_guard (m n f : Bool) :
    (Bool.xor m n && f) = Bool.xor (m && f) (n && f) := by
  cases m <;> cases n <;> cases f <;> decide

theorem hmr_dressing (m q d : Bool) :
    Bool.xor (m && Bool.xor q d) (m && d) = (m && q) := by
  cases m <;> cases q <;> cases d <;> decide

theorem joint_absorption (m n a b p1 p2 p3 : Bool)
    (h : parity [p1,p2,p3] = Bool.xor (m && a) (n && b)) :
    parity [m && a,n && b,p1,p2,p3] = false := by
  change parity ([m && a,n && b] ++ [p1,p2,p3]) = false
  rw [parity_append, h]
  cases m <;> cases n <;> cases a <;> cases b <;> decide

def prefixBits (prev : Bool) : List Bool → List Bool
  | [] => []
  | m :: ms =>
    let n := Bool.xor m prev
    n :: prefixBits n ms

def recover (prev : Bool) : List Bool → List Bool
  | [] => []
  | n :: ns => Bool.xor n prev :: recover n ns

theorem recover_prefix (ms : List Bool) (prev : Bool) :
    recover prev (prefixBits prev ms) = ms := by
  induction ms generalizing prev with
  | nil => rfl
  | cons m ms ih =>
    cases prev <;> cases m <;> simp [prefixBits, recover, ih]

theorem prefix_recover (ns : List Bool) (prev : Bool) :
    prefixBits prev (recover prev ns) = ns := by
  induction ns generalizing prev with
  | nil => rfl
  | cons n ns ih =>
    cases prev <;> cases n <;> simp [prefixBits, recover, ih]

def headCarry : List (Bool × Bool) → Bool
  | [] => false
  | (_, c) :: _ => c

def oldPhase (prev : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (n,c) :: xs =>
    Bool.xor (Bool.xor n prev && c) (oldPhase n xs)

def carryPhase : List (Bool × Bool) → Bool
  | [] => false
  | (n,c) :: xs =>
    Bool.xor (n && Bool.xor c (headCarry xs)) (carryPhase xs)

theorem carry_phase_telescoping (xs : List (Bool × Bool)) (prev : Bool) :
    oldPhase prev xs = Bool.xor (prev && headCarry xs) (carryPhase xs) := by
  induction xs generalizing prev with
  | nil => cases prev <;> rfl
  | cons v xs ih =>
    rcases v with ⟨n,c⟩
    change Bool.xor (Bool.xor n prev && c) (oldPhase n xs) =
      Bool.xor (prev && c) (Bool.xor (n && Bool.xor c (headCarry xs)) (carryPhase xs))
    rw [ih n]
    cases hc : headCarry xs <;> cases hp : carryPhase xs <;>
      cases prev <;> cases n <;> cases c <;> rfl

theorem carry_phase_rebase (xs : List (Bool × Bool)) :
    oldPhase false xs = carryPhase xs := by
  rw [carry_phase_telescoping]
  cases headCarry xs <;> cases carryPhase xs <;> rfl

-- Actual V27 low/dress parent: HMRs 7812 and 8167, both q35,
-- each with inserted CX(15,35). Removed observations 26107,27181,27261.
-- The Boolean identity below uses the BDD-extracted equality as a premise.
theorem actual_low_joint (m519 m539 q15a q15b p1 p2 p3 : Bool)
    (h : parity [p1,p2,p3] = Bool.xor (m519 && q15a) (m539 && q15b)) :
    parity [m519 && q15a,m539 && q15b,p1,p2,p3] = false :=
  joint_absorption m519 m539 q15a q15b p1 p2 p3 h

theorem command_counts :
    56734 - 40 - 42 - 59 - 448 = 56145 ∧
    53049 - 7 - 36 - 31 - 439 = 52536 ∧
    57035 - 56694 = 341 := by decide

theorem width_scope :
    7504 > 0 ∧ 5785 > 0 ∧ 22501 = 1406 * 16 + 5 ∧
    22725 = 1420 * 16 + 5 := by decide

end GVQCC.V27
