import Std
namespace GVQCC.CrossTaskLiveTensor
def bx (a b : Bool) : Bool := Bool.xor a b
theorem guarded_factor (g a b c : Bool) :
    bx (g && a && b) (g && a && c) = (g && a && bx b c) := by
  cases g <;> cases a <;> cases b <;> cases c <;> decide
theorem dirty_broadcast (a b t u : Bool) :
    bx (bx u t) (bx t (a && b)) = bx u (a && b) := by
  cases a <;> cases b <;> cases t <;> cases u <;> decide
theorem early_measurement (x g a b m : Bool) :
    (m && bx x (g && a && b)) =
    bx (m && x) (m && g && a && b) := by
  cases x <;> cases g <;> cases a <;> cases b <;> cases m <;> decide
theorem phase_bridge (t p q g : Bool) :
    bx (t && q) (bx t (g && p) && q) = (g && p && q) := by
  cases t <;> cases p <;> cases q <;> cases g <;> decide
theorem zero_release (g : Bool) : (false && !g) = false := by
  cases g <;> decide
end GVQCC.CrossTaskLiveTensor
#print axioms GVQCC.CrossTaskLiveTensor.guarded_factor
#print axioms GVQCC.CrossTaskLiveTensor.dirty_broadcast
#print axioms GVQCC.CrossTaskLiveTensor.early_measurement
#print axioms GVQCC.CrossTaskLiveTensor.phase_bridge
#print axioms GVQCC.CrossTaskLiveTensor.zero_release
