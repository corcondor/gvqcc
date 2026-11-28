import Init
namespace DQI316K
def ccx (a b t : Bool) : Bool := t ^^ (a && b)
def cx (a b : Bool) : Bool := a ^^ b
def gate (k a b t : Bool) : Bool := t ^^ (k && a && b)
theorem guarded_factor (k a b c t : Bool) :
  gate k a c (gate k a b t) = gate k a (c ^^ b) t := by
  cases k <;> cases a <;> cases b <;> cases c <;> cases t <;> decide
theorem guarded_conjugation (k b c : Bool) :
  (c ^^ (k && b)) ^^ (k && b) = c := by
  cases k <;> cases b <;> cases c <;> decide
theorem guarded_cancel (k a b t : Bool) :
  gate k a b (gate k a b t) = t := by
  cases k <;> cases a <;> cases b <;> cases t <;> decide
theorem measured_product (m a b p : Bool) :
  (p ^^ (m && (a && b))) ^^ (if m then a && b else false) = p := by
  cases m <;> cases a <;> cases b <;> cases p <;> decide
theorem conditional_repayment (m d z p : Bool) :
  (p ^^ (d && m && z)) ^^ (if d then (if m then z else false) else false) = p := by
  cases m <;> cases d <;> cases z <;> cases p <;> decide
theorem block_zero_phase (d z p : Bool) :
  (p ^^ (d && z)) ^^ (d && z) = p := by
  cases d <;> cases z <;> cases p <;> decide
theorem phase_outside_guard (d p : Bool) : p ^^ (d && false) = p := by
  cases d <;> cases p <;> decide
#print axioms guarded_factor
#print axioms guarded_conjugation
#print axioms guarded_cancel
#print axioms measured_product
#print axioms conditional_repayment
#print axioms block_zero_phase
#print axioms phase_outside_guard
end DQI316K
