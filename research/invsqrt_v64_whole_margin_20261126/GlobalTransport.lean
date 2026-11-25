import Init
namespace GlobalTransport

theorem carry_transport (m c b : Bool) :
    Bool.xor true (m && Bool.xor true (Bool.xor c (b && m))) =
      Bool.xor (Bool.xor (Bool.xor true m) (m && c)) (b && m) := by
  cases m <;> cases c <;> cases b <;> decide

theorem conditional_basis (f a b : Bool) :
    (f && Bool.xor a b) = Bool.xor (f && a) (f && b) := by
  cases f <;> cases a <;> cases b <;> decide

theorem abel_three (a b c u v w : Bool) :
    Bool.xor (Bool.xor (a && u) (b && v)) (c && w) =
      Bool.xor (Bool.xor ((Bool.xor (Bool.xor a b) c) && w)
        (a && Bool.xor u v)) ((Bool.xor a b) && Bool.xor v w) := by
  cases a <;> cases b <;> cases c <;> cases u <;> cases v <;> cases w <;> decide

theorem transported_measurement_debt (h f a b : Bool) :
    (h && (f && Bool.xor a b)) = Bool.xor (h && (f && a)) (h && (f && b)) := by
  cases h <;> cases f <;> cases a <;> cases b <;> decide

end GlobalTransport
