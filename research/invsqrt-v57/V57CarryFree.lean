import Std.Tactic
namespace GVQCC.V57
def bx (a b : Bool) : Bool := Bool.xor a b
def bit (a : Bool) : Nat := if a then 1 else 0
def majority (a b c : Bool) : Bool := bx a (bx a b && bx a c)
theorem compressor (a b c : Bool) :
    bit a + bit b + bit c = bit (bx (bx a b) c) + 2 * bit (majority a b c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem exclusive_readout (a b : Bool) (h : (a && b) = false) :
    bit a + bit b = bit (bx a b) := by
  cases a <;> cases b <;> simp_all [bit, bx, Bool.xor]
theorem quadratic_delta (a b da db : Bool) :
    bx (bx a da && bx b db) (a && b) =
      bx (bx (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
theorem abel (m n a b : Bool) :
    bx (m && a) (n && b) = bx (bx m n && a) (n && bx a b) := by
  cases m <;> cases n <;> cases a <;> cases b <;> decide
theorem phase_factor (m a b c : Bool) :
    (m && bx (a && b) (a && c)) = bx (m && a && b) (m && a && c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide
theorem square_expansion (u v : Int) :
    (u+v)*(u+v) = u*u + (u*v + u*v) + v*v := by
  simp only [Int.add_mul, Int.mul_add]
  rw [Int.mul_comm v u]
  omega
theorem fused_horner2 (c2 c3 c4 t d : Int) :
    (c4*t+c3*d)*t+c2*d*d = c4*t*t+c3*d*t+c2*d*d := by
  rw [Int.add_mul]
theorem quotient_remainder_transport (u v d q1 q2 r1 r2 : Int)
    (h1 : u = d*q1+r1) (h2 : v = d*q2+r2) :
    u+v = d*(q1+q2)+(r1+r2) := by
  rw [h1,h2,Int.mul_add]
  omega
theorem interval_update (l u z delta : Int)
    (h : l-z ≤ delta ∧ delta ≤ u-z) : l ≤ z+delta ∧ z+delta ≤ u := by
  omega
theorem simultaneous_overlap (l u z da db : Int)
    (h : l-z ≤ da+db ∧ da+db ≤ u-z) :
    l ≤ z+da+db ∧ z+da+db ≤ u := by omega
theorem budget_check : 6998 - 2222 = (4776 : Nat) ∧
    143 - 105 = (38 : Nat) ∧ 8985 - 3552 = (5433 : Nat) := by decide
end GVQCC.V57
