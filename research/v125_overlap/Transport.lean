import Std
namespace GVQCC.V125
def bx (a b : Bool) : Bool := Bool.xor a b

-- The carrier may be dirty: the two CXs remove its initial value.
theorem dirty_fanout (a b x y : Bool) :
    (bx x (a && b), bx (bx y x) (bx x (a && b))) =
    (bx x (a && b), bx y (a && b)) := by
  cases a <;> cases b <;> cases x <;> cases y <;> decide

def writes (x : Bool) (ws : List Bool) : Bool := ws.foldl bx x

-- Delivery can cross any intervening target-only XOR writes, but not a
-- read, phase, swap, reset, or measurement of the receiving wire.
theorem write_transport (x p : Bool) (ws : List Bool) :
    writes (bx x p) ws = bx (writes x ws) p := by
  induction ws generalizing x with
  | nil => rfl
  | cons a rest ih =>
    change writes (bx (bx x p) a) rest = bx (writes (bx x a) rest) p
    have h : bx (bx x p) a = bx (bx x a) p := by
      cases x <;> cases p <;> cases a <;> decide
    rw [h, ih]

theorem early_delivery (a b x y : Bool) (ws : List Bool) :
    (bx x (a && b), writes (bx (bx y x) (bx x (a && b))) ws) =
      (bx x (a && b), bx (writes y ws) (a && b)) := by
  have h : bx (bx y x) (bx x (a && b)) = bx y (a && b) := by
    cases a <;> cases b <;> cases x <;> cases y <;> decide
  rw [h, write_transport]

-- Retained product with one affine correction and arbitrary HMR outcome.
def corr (a b l r c : Bool) := bx (l && a) (bx (r && b) c)
theorem retained_correct (a b l r c t m : Bool) :
    let p := bx (a && b) (corr a b l r c)
    (bx (bx t p) (corr a b l r c),
      bx (m && p) (bx (m && a && b)
        (bx (m && l && a) (bx (m && r && b) (m && c))))) =
      (bx t (a && b), false) := by
  cases a <;> cases b <;> cases l <;> cases r <;> cases c <;> cases t <;> cases m <;> decide

#print axioms dirty_fanout
#print axioms write_transport
#print axioms early_delivery
#print axioms retained_correct
end GVQCC.V125
