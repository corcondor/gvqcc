import Std.Tactic
namespace GVQCC.V47

def x (a b : Bool) : Bool := Bool.xor a b

theorem merge_shared (a b c d : Bool) :
    x (a && b && c) (a && b && d) = (a && b && x c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem dirty_accumulator (t s h q : Bool) :
    (x (x t (s && h)) (s && x h q), x (x h q) q) =
      (x t (s && q), h) := by
  cases t <;> cases s <;> cases h <;> cases q <;> decide

theorem cube_reorient (s a b : Bool) : (s && a && b) = (a && b && s) := by
  cases s <;> cases a <;> cases b <;> decide

theorem deferred_measurement (m q : Bool) : x (m && q) (m && q) = false := by
  cases m <;> cases q <;> decide

theorem phase_transport (m a da b db : Bool) :
    x (m && (x a da && x b db)) (m && a && b) =
      x (x (m && a && db) (m && b && da)) (m && da && db) := by
  cases m <;> cases a <;> cases da <;> cases b <;> cases db <;> decide

theorem abel_step (p c m d z : Bool) :
    x (p && c) (x (m && x c d) z) =
      x (x p m && c) (x (m && d) z) := by
  cases p <;> cases c <;> cases m <;> cases d <;> cases z <;> decide

def butterfly (a b : Int) : Int × Int := (a+b,a-b)

theorem butterfly_inverse (a b : Int) :
    butterfly (butterfly a b).1 (butterfly a b).2 = (2*a,2*b) := by
  unfold butterfly
  congr 1 <;> omega

theorem budget_counts :
    214 - 97 = 117 ∧ 37 - 32 = 5 ∧ 686 - 291 = 395 ∧
    113183 - 48889 = 64294 ∧ 3059 * 37 = 113183 := by decide

end GVQCC.V47
