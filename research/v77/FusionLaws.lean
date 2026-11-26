import Init

def bitI (b : Bool) : Int := if b then 1 else 0

theorem conditional_clean_step (g t x y : Bool) (h : g = true → t = true) :
    (g && !(Bool.xor t (x && y))) = (g && x && y) := by
  cases g <;> cases t <;> cases x <;> cases y <;> simp_all [Bool.xor]

theorem phase_echo (s f p : Bool) :
    bitI (Bool.xor s (f && p)) - bitI s =
    (1 - 2 * bitI s) * bitI f * bitI p := by
  cases s <;> cases f <;> cases p <;> decide

theorem shared_factor (u v w : Bool) :
    (u && Bool.xor v w) = Bool.xor (u && v) (u && w) := by
  cases u <;> cases v <;> cases w <;> decide

theorem product_delta (a b da db : Bool) :
    Bool.xor (Bool.xor a da && Bool.xor b db) (a && b) =
      Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem dual_phase (p q m n : Bool) :
    Bool.xor (m && p) (n && q) =
      Bool.xor (Bool.xor m n && p) (n && Bool.xor p q) := by
  cases p <;> cases q <;> cases m <;> cases n <;> decide
