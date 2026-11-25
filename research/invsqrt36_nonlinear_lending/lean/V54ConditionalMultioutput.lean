import Std.Tactic
namespace GVQCC.V54
def x (a b : Bool) := Bool.xor a b
theorem guarded_clean (h d p b : Bool) :
    (h && d) = false → (h && x d (p && b)) = (h && p && b) := by
  cases h <;> cases d <;> cases p <;> cases b <;> decide
theorem sibling_delta (d p b : Bool) :
    x (x d (p && !b)) p = x d (p && b) := by
  cases d <;> cases p <;> cases b <;> decide
theorem guarded_transfer (h d p b t : Bool) :
    (h && d) = false → x t (h && x d (p && b)) = x t (h && p && b) := by
  cases h <;> cases d <;> cases p <;> cases b <;> cases t <;> decide
theorem restore_dirty (d a : Bool) : x (x d a) a = d := by
  cases d <;> cases a <;> decide
theorem interval_obstruction (l u q : Int) (h : u < l) :
    ¬ (l ≤ q ∧ q ≤ u) := by omega
theorem signed_bit (a z : Bool) (d : Int) :
    (if a then -d * (if z then 0 else 1) else d * (if z then 1 else 0)) =
      d * ((if z then 1 else 0) - (if a then 1 else 0)) := by
  cases a <;> cases z <;> simp <;> omega
theorem count_31 : 27 + 4 = (31 : Nat) ∧ 20 + 11 = (31 : Nat) := by decide
end GVQCC.V54
