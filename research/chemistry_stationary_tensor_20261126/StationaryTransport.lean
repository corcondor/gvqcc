import Std

-- Circuit-specific reachability is a separate executable check.
theorem factor_transport (a b l : Bool) :
    Bool.xor l (a && b) = (if a then Bool.xor l b else l) := by
  cases a <;> cases b <;> cases l <;> decide

theorem triangle_transport (d e p q r : Bool) :
    Bool.xor (Bool.xor (d && p) (e && q)) ((Bool.xor d e) && r) =
      Bool.xor (d && Bool.xor p r) (e && Bool.xor q r) := by
  cases d <;> cases e <;> cases p <;> cases q <;> cases r <;> decide

theorem discrete_abel (a b m n : Bool) :
    Bool.xor (a && m) (b && n) =
      Bool.xor (a && Bool.xor m n) (Bool.xor a b && n) := by
  cases a <;> cases b <;> cases m <;> cases n <;> decide

theorem controlled_transport (a b c d : Bool) :
    Bool.xor ((Bool.xor a c) && (Bool.xor b d)) (a && b) =
      Bool.xor (Bool.xor (a && d) (b && c)) (c && d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
