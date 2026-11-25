import Std.Tactic
namespace GVQCC.V43
def X := Bool.xor

-- Pull back the pending phase when a physical target is toggled.
theorem quadratic_pullback (m t a b c : Bool) :
    (m && X t (a && b) && c) =
      X (m && t && c) (m && a && b && c) := by
  cases m <;> cases t <;> cases a <;> cases b <;> cases c <;> decide

-- A measured product can carry a phase debt through a second update.
theorem temporal_debt (p m f h k : Bool) :
    X (X (X p (m && f)) (m && h)) (m && k) =
      X p (m && X (X f h) k) := by
  cases p <;> cases m <;> cases f <;> cases h <;> cases k <;> decide

-- Source PR103 [9380,9396): fourteen CX into q36 have a combined
-- XOR l, independent of the measured q21. Both sides keep the HMR
-- outcome and the sign m*b, as well as the final target.
def original (t l a b m : Bool) : Bool × Bool × Bool :=
  (X (X t l) (a && b), false, m && b)
def transported (t l a b m : Bool) : Bool × Bool × Bool :=
  (X (X t (a && b)) l, false, m && b)
theorem actual9380 (t l a b m : Bool) :
    original t l a b m = transported t l a b m := by
  cases t <;> cases l <;> cases a <;> cases b <;> cases m <;> decide

-- Matrix-factor gauge over GF(2) for shared terms.
theorem gauge (a b u v : Bool) :
    X (a && u) (b && v) =
      X (X a b && u) (b && X u v) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide

theorem receipts : 2899 - 80 = 2819 ∧ 2899 - 113 = 2786 ∧
  23143 + 80 = 23223 ∧ 576 + 24 + 4096 = 4696 := by decide
end GVQCC.V43
