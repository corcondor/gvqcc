import Std
namespace V46
def bx (a b : Bool) : Bool := Bool.xor a b

-- Quadratic phase tensor under an elementary CNOT shear.
theorem shear_phase (a b c : Bool) :
    (bx a b && c) = bx (a && c) (b && c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem shear_square (a b : Bool) :
    (bx a b && bx a b) = bx a b := by
  cases a <;> cases b <;> decide

theorem shear_self (a b : Bool) :
    (bx a b && b) = bx (a && b) b := by
  cases a <;> cases b <;> decide

theorem shear_inverse (a b : Bool) : bx (bx a b) b = a := by
  cases a <;> cases b <;> decide

-- Two guard rows of the phase tensor share a single classical parity.
theorem guard_rectangle (g h p q : Bool) :
    bx (bx (g && p) (h && p)) (bx (g && q) (h && q)) =
      (bx g h && bx p q) := by
  cases g <;> cases h <;> cases p <;> cases q <;> decide

theorem guard_product (g h a b : Bool) :
    bx (g && a && b) (h && a && b) = (bx g h && a && b) := by
  cases g <;> cases h <;> cases a <;> cases b <;> decide

-- A common factor shared by two successive observations.
theorem carry_factor (a b c : Bool) :
    (b && bx (a && b) c) = (b && bx a c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem abel (u v u' v' : Bool) :
    bx (u && v) (u' && v') =
      bx (u && bx v v') (bx u u' && v') := by
  cases u <;> cases v <;> cases u' <;> cases v' <;> decide

theorem measurement_debt (m x y z : Bool) :
    bx (m && bx x y) (m && bx y z) = (m && bx x z) := by
  cases m <;> cases x <;> cases y <;> cases z <;> decide

-- Rank-one transvection on an output coordinate. Valid when the
-- factor-control coordinates are invariant under the transvection.
theorem transvection_inverse (x d a b : Bool) :
    bx (bx x (d && a && b)) (d && a && b) = x := by
  cases x <;> cases d <;> cases a <;> cases b <;> decide

-- Direct affine conditional carry decoder. Premise is a care-set relation.
theorem cofactor (a b c f : Bool) (h : b = false → f = c) :
    bx (a && b) c = bx f (b && bx (bx a c) f) := by
  cases b
  · have hf := h rfl
    subst f
    cases a <;> cases c <;> decide
  · cases a <;> cases c <;> cases f <;> decide

-- Product of two affine parities expands to a transported bilinear tensor.
theorem quadratic_transport (a b c d : Bool) :
    (bx a b && bx c d) =
      bx (bx (a && c) (a && d)) (bx (b && c) (b && d)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
end V46
