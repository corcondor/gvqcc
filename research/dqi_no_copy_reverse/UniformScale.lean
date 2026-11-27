import Lean

namespace GVQCC.UniformScale
abbrev bx := Bool.xor
abbrev bn := Bool.not

theorem pivot_correction (a v f c g y : Bool)
    (hy : y = bx (v && a) f) (ha : a = bx (c && y) g) :
    bx (bx a f) (bn v && bx (c && f) g) = y := by
  revert hy ha
  cases a <;> cases v <;> cases f <;> cases c <;> cases g <;> cases y <;> decide

theorem transport (a d v c f : Bool) :
    let z0 := bx a (c && d)
    let d0 := bx d (bn v && z0)
    let z1 := bx z0 f
    let d1 := bx d0 (bn v && z1)
    let z2 := bx z1 (c && d1)
    z2 = bx (bx a f) (c && (bn v && f)) ∧ d1 = bx d (bn v && f) := by
  cases a <;> cases d <;> cases v <;> cases c <;> cases f <;> decide

theorem dirty_restore (d v a f : Bool) :
    bx (bx d (bn v && f)) (bn v && bx (v && a) f) = d := by
  cases d <;> cases v <;> cases a <;> cases f <;> decide

theorem phase_transport (a y c g x m p : Bool)
    (ha : a = bx (c && y) g) :
    bx (bx (bx p (m && bx x g)) (m && bx x a)) (m && (c && y)) = p := by
  revert ha
  cases a <;> cases y <;> cases c <;> cases g <;> cases x <;> cases m <;> cases p <;> decide

theorem dirty_commutator (p d a f : Bool) :
    bx (bx p (a && d)) (a && bx d f) = bx p (a && f) := by
  cases p <;> cases d <;> cases a <;> cases f <;> decide

/-- Effective scalar selects the identity coordinate if the quantum control is off. -/
theorem virtual_scalar (flag s k : Bool) :
    bx k (flag && bx s k) = (if flag then s else k) := by
  cases flag <;> cases s <;> cases k <;> decide

/-- Four borrowed-bit CCX gates implement the conditional product and restore
    the helper; the same Boolean difference applies to a phase target. -/
theorem controlled_borrow (r h flag s target : Bool) :
    let h' := bx h (flag && s)
    bx (bx target (h && r)) (h' && r) = bx target (flag && s && r) ∧
      bx h' (flag && s) = h := by
  cases r <;> cases h <;> cases flag <;> cases s <;> cases target <;> decide

end GVQCC.UniformScale
#print axioms GVQCC.UniformScale.pivot_correction
#print axioms GVQCC.UniformScale.transport
#print axioms GVQCC.UniformScale.dirty_restore
#print axioms GVQCC.UniformScale.phase_transport
#print axioms GVQCC.UniformScale.dirty_commutator
#print axioms GVQCC.UniformScale.virtual_scalar
#print axioms GVQCC.UniformScale.controlled_borrow
