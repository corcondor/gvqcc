import Std.Tactic.BVDecide

namespace GVQCCVirtualBoundary
def bx := Bool.xor
def phi (t x y : Bool) : Bool := t && bx true (bx x y)
def delta (a b c : Bool) : Bool := bx (bx (a && b) a) c

theorem boundary_phase (t f h : Bool) :
    (f && h) = bx (t && h) ((bx t f) && h) := by
  cases t <;> cases f <;> cases h <;> decide

theorem pr54_potential (a b c x y t : Bool) :
    (delta a b c && bx true (bx x y)) =
    bx (phi t x y) (phi (bx t (delta a b c)) x y) := by
  cases a <;> cases b <;> cases c <;> cases x <;> cases y <;> cases t <;> decide

theorem two_steps (t f g h : Bool) :
    bx (f && h) (g && h) =
    bx (t && h) ((bx (bx t f) g) && h) := by
  cases t <;> cases f <;> cases g <;> cases h <;> decide

def parity : List Bool → Bool
  | [] => false
  | a :: rest => bx a (parity rest)

theorem telescoping (ds : List Bool) (t h : Bool) :
    parity (ds.map (fun d => d && h)) =
    bx (t && h) ((bx t (parity ds)) && h) := by
  induction ds generalizing t with
  | nil => cases t <;> cases h <;> decide
  | cons d ds ih =>
    simp only [List.map, parity]
    rw [ih (bx t d)]
    cases t <;> cases d <;> cases h <;> cases parity ds <;> decide

end GVQCCVirtualBoundary
