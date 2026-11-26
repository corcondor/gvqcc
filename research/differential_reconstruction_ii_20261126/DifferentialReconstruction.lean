import Mathlib
-- Local Boolean identities only; not native KickMix semantics.
def dx (a b : Bool) : Bool := xor a b
theorem diff_step (x y u v : Bool) :
    dx ((dx x u) && (dx y v)) (x && y) =
      dx (dx (x && v) (y && u)) (u && v) := by
  cases x <;> cases y <;> cases u <;> cases v <;> decide
theorem terminal_debt (m t p : Bool) :
    (m && dx t p) = dx (m && t) (m && p) := by
  cases m <;> cases t <;> cases p <;> decide
theorem recover_product (t p r : Bool) (h : r = dx t p) :
    dx t r = p := by
  subst r
  cases t <;> cases p <;> decide
theorem phase_cancel (m p : Bool) : dx (m && p) (m && p) = false := by
  cases m <;> cases p <;> decide
theorem complemented_control (a b : Bool) :
    (!a && b) = dx b (a && b) := by
  cases a <;> cases b <;> decide
