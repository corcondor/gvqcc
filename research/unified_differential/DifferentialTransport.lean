import Mathlib

def bx (a b : Bool) : Bool := Bool.xor a b

theorem diff_product (u v du dv : Bool) :
    bx ((bx u du) && (bx v dv)) (u && v) =
      bx (bx (u && dv) (v && du)) (du && dv) := by
  cases u <;> cases v <;> cases du <;> cases dv <;> decide

theorem same_factor (h a b : Bool) :
    bx (h && a) (h && b) = h && (bx a b) := by
  cases h <;> cases a <;> cases b <;> decide

theorem change_plane_basis (a b : Bool) :
    a && (bx a b) = bx (a && b) a := by
  cases a <;> cases b <;> decide

theorem carry_difference (a b c : Bool) :
    bx (bx (a && b) (bx (a && c) (b && c))) c =
      (bx a c) && (bx b c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem diff_phase_factor (h a b m : Bool) :
    bx (m && h && a) (m && h && b) = m && h && bx a b := by
  cases h <;> cases a <;> cases b <;> cases m <;> decide
