import Mathlib

namespace GVQCC.UniformScale
abbrev bx := Bool.xor
abbrev bn := Bool.not

theorem pivot_correction (a v f c g y : Bool)
    (hy : y = bx (v && a) f) (ha : a = bx (c && y) g) :
    bx (bx a f) (bn v && bx (c && f) g) = y := by
  cases a <;> cases v <;> cases f <;> cases c <;> cases g <;> cases y <;> simp_all [bx, bn, Bool.xor, Bool.not]

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
  cases a <;> cases y <;> cases c <;> cases g <;> cases x <;> cases m <;> cases p <;> simp_all [bx, Bool.xor]

theorem dirty_commutator (p d a f : Bool) :
    bx (bx p (a && d)) (a && bx d f) = bx p (a && f) := by
  cases p <;> cases d <;> cases a <;> cases f <;> decide

end GVQCC.UniformScale
#print axioms GVQCC.UniformScale.pivot_correction
#print axioms GVQCC.UniformScale.transport
#print axioms GVQCC.UniformScale.dirty_restore
#print axioms GVQCC.UniformScale.phase_transport
#print axioms GVQCC.UniformScale.dirty_commutator
