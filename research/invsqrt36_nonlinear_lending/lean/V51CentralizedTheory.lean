import Std.Tactic
namespace GVQCC.V51
def x (a b : Bool) : Bool := Bool.xor a b
def bit (a : Bool) : Int := if a then 1 else 0

theorem sibling_transport (p b : Bool) :
    x (p && !b) p = (p && b) := by
  cases p <;> cases b <;> decide

theorem sibling_restore (p b : Bool) :
    x (x (p && !b) p) (p && b) = false := by
  cases p <;> cases b <;> decide

theorem persistent_gauge (q p delta : Bool) :
    x (x (x q p) delta) p = x q delta := by
  cases q <;> cases p <;> cases delta <;> decide

theorem dirty_factor (f d g t : Bool) :
    x (x t (x d f && g)) (d && g) = x t (f && g) := by
  cases f <;> cases d <;> cases g <;> cases t <;> decide

theorem dirty_pair (f d g h t u : Bool) :
    (x (x d f) f, x (x t (x d f && g)) (d && g),
      x (x u (x d f && h)) (d && h)) =
    (d, x t (f && g), x u (f && h)) := by
  cases f <;> cases d <;> cases g <;> cases h <;> cases t <;> cases u <;> decide

theorem quadratic_transport (a b da db : Bool) :
    x ((x a da) && (x b db)) (a && b) =
      x (x (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem abel_transport (m0 m1 f0 f1 : Bool) :
    x (m1 && f1) (m0 && f0) =
      x ((x m1 m0) && f1) (m0 && (x f1 f0)) := by
  cases m0 <;> cases m1 <;> cases f0 <;> cases f1 <;> decide

theorem signed_phase (f p : Bool) (w : Int) :
    w * bit (x f p) - w * bit p = w * bit f * (1 - 2 * bit p) := by
  cases f <;> cases p <;> simp [x, bit] <;> omega

theorem counts :
    274 - 160 = 114 ∧ 81891 - 50157 = 31734 ∧
    18787 - 14553 = 4234 ∧ 25976 - 21904 = 4072 := by decide
end GVQCC.V51
