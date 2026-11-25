import Std.Tactic
namespace GVQCC.V65
def bx (a b : Bool) := Bool.xor a b
theorem shared_flag (f a b : Bool) :
    bx (f && a) (f && b) = (f && bx a b) := by
  cases f <;> cases a <;> cases b <;> decide
theorem quadratic_transport (a b da db : Bool) :
    bx (bx a da && bx b db) (a && b) =
      bx (bx (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
theorem abel (a b f g : Bool) :
    bx (f && a) (g && b) = bx (bx f g && a) (g && bx a b) := by
  cases a <;> cases b <;> cases f <;> cases g <;> decide
theorem square_symmetry (a b : Int) :
    (a+b)*(a+b) = a*a + 2*(a*b) + b*b := by
  rw [Int.add_mul, Int.mul_add, Int.mul_add, Int.mul_comm b a]
  omega
theorem rounding_transport (c a w : Int) :
    (c+a+8*w+8)/16 = ((c+a+8)/8+w)/2 := by omega
theorem rounded_numerator_transport (c w : Int) :
    (c+131072*w+8192)/16384 = (c+8192)/16384+8*w := by omega
theorem low_word_transport (z : Int) :
    ((z%32)/2)%16 = (z/2)%16 := by omega
theorem parity_phase_cleanup (a b t : Bool) :
    bx (bx t (a && b)) (a && b) = t := by
  cases a <;> cases b <;> cases t <;> decide
end GVQCC.V65
