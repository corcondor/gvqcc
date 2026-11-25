import Std.Tactic
namespace GVQCC.V63
def bx (a b : Bool) := Bool.xor a b
theorem carry_transport (m c b : Bool) :
    bx true (m && !(bx c (b && m))) =
    bx (bx (bx true m) (m && c)) (b && m) := by
  cases m <;> cases c <;> cases b <;> decide
theorem product_delta (a b da db : Bool) :
    bx (bx a da && bx b db) (a && b) =
    bx (bx (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
theorem abel (m n a b : Bool) :
    bx (m && a) (n && b) = bx (bx m n && a) (n && bx a b) := by
  cases m <;> cases n <;> cases a <;> cases b <;> decide
theorem mux_debt (h f w : Bool) :
    bx f (h && bx f w) = (if h then w else f) := by
  cases h <;> cases f <;> cases w <;> decide
theorem no_borrow_symmetry (a q : Int)
    (ha : 0 ≤ a ∧ a < 8192) (hq : 0 ≤ q ∧ q < 8192) :
    (q ≤ a) ↔ ((a-q)%8192 ≤ a) := by omega
theorem reflection_involution (a q : Int)
    (ha : 0 ≤ a ∧ a < 8192) (hq : 0 ≤ q ∧ q < 8192) :
    (a-(a-q)%8192)%8192 = q := by omega
theorem reflect_high (c q : Int) (hq : 0 ≤ q ∧ q < 8192) :
    (c-q)/8192 = c/8192 - (if q ≤ c%8192 then 0 else 1) := by
  split <;> omega
end GVQCC.V63
