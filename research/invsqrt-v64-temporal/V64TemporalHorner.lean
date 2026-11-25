import Init
namespace V64TemporalHorner
theorem rolling (a b : Bool) : Bool.xor a (Bool.xor a b) = b := by
  cases a <;> cases b <;> decide
theorem rolling_factor (a b l p q : Bool)
    (h : Bool.xor a b = Bool.xor l (p && q)) :
    Bool.xor a (Bool.xor l (p && q)) = b := by
  rw [← h]
  exact rolling a b
theorem debt_zero (m a b : Bool) (h : a = b) :
    Bool.xor (m && a) (m && b) = false := by
  subst b
  cases m <;> cases a <;> decide
theorem rolling_two (a b c : Bool) :
    Bool.xor (Bool.xor a (Bool.xor a b)) (Bool.xor b c) = c := by
  rw [rolling, rolling]
end V64TemporalHorner
