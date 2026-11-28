import Init
import Std
namespace GVQCC.CentralGauge
def choose (oldCount newCount : Nat) : Bool := newCount < oldCount
theorem support_monotone (o n : Nat) : (if choose o n then n else o) â¤ o := by
  by_cases h : n < o
  Â· simpa [choose, h] using Nat.le_of_lt h
  Â· simp [choose, h]
theorem compensate (p h : Bool) : Bool.xor (Bool.xor p h) h = p := by
  cases p <;> cases h <;> decide
theorem selected_phase (old gauge : Bool) (take : Bool) :
    (if take then Bool.xor gauge (Bool.xor old gauge) else old) = old := by
  cases old <;> cases gauge <;> cases take <;> decide
theorem linear_phase_split (a b c : Bool) :
    (a && Bool.xor b c) = Bool.xor (a && b) (a && c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem carry_step (x c : Bool) :
    (if x then 1 else 0) + (if c then 1 else 0) =
      (if Bool.xor x c then 1 else 0) + 2*(if x && c then 1 else 0) := by
  cases x <;> cases c <;> decide
#print axioms support_monotone
#print axioms compensate
#print axioms selected_phase
#print axioms linear_phase_split
#print axioms carry_step
end GVQCC.CentralGauge

