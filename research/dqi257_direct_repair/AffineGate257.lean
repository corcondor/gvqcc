import Std
namespace DQI257
theorem shared_product (a b x y : Bool) :
    ((x ^^ (a && b)) ^^ (y ^^ (a && b))) = (x ^^ y) := by
  cases a <;> cases b <;> cases x <;> cases y <;> decide
theorem phase_repay (a b t u : Bool) :
    ((t && u) ^^ ((t ^^ (a && b)) && u)) = ((a && b) && u) := by
  cases a <;> cases b <;> cases t <;> cases u <;> decide
theorem product_change_of_frame (a b : Bool) :
    (a && (a ^^ b)) = (a ^^ (a && b)) := by
  cases a <;> cases b <;> decide
def accept (value phase dirty mask paid parent : Nat) : Prop :=
  value = 0 ∧ phase = 0 ∧ dirty = 0 ∧ mask = 0 ∧ paid < parent
theorem reject_increase (v p d m c b : Nat) (h : b ≤ c) :
    ¬ accept v p d m c b := by
  intro h1
  exact Nat.not_lt_of_ge h h1.2.2.2.2
theorem reject_value_error (v p d m c b : Nat) (h : v ≠ 0) :
    ¬ accept v p d m c b := by
  intro h1
  exact h h1.1
#print axioms shared_product
#print axioms phase_repay
#print axioms product_change_of_frame
#print axioms reject_increase
#print axioms reject_value_error
end DQI257
