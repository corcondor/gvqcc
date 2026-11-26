import Std
namespace V71
def x (a b : Bool) : Bool := Bool.xor a b
theorem factor_flip (f g k d h : Bool) :
    x (f && g && d) (f && k && h) =
    x (f && x g k && d) (f && k && x h d) := by
  cases f <;> cases g <;> cases k <;> cases d <;> cases h <;> decide
theorem output_flip (a b c e d : Bool) :
    x (a && b && d) (c && e && d) =
    x (a && x b e && d) (x c a && e && d) := by
  cases a <;> cases b <;> cases c <;> cases e <;> cases d <;> decide
theorem plus_split (a b f d : Bool) :
    (a && b && d) = x (a && x b f && d) (a && f && d) := by
  cases a <;> cases b <;> cases f <;> cases d <;> decide
theorem abel (u v w z : Bool) :
    x (u && v) (w && z) = x (u && x v z) (x u w && z) := by
  cases u <;> cases v <;> cases w <;> cases z <;> decide
theorem carrier_delta (g h : Bool) : x g (x g h) = h := by
  cases g <;> cases h <;> decide
theorem dependent_delta (g h k p : Bool)
    (H : x g h = x k p) : x (x g k) p = h := by
  cases g <;> cases h <;> cases k <;> cases p <;> simp [x, Bool.xor] at *
theorem private_debt (m g : Bool) : x (m && g) (m && g) = false := by
  cases m <;> cases g <;> decide
end V71
