import Std.Tactic

namespace V55
def bx (a b : Bool) : Bool := if a then !b else b

-- Shared dyadic residual, compared to the unfactored ESOP.
def shared (p15 p31 p63 a b c d e : Bool) : Bool :=
  bx (bx p63 p31)
    (bx ((p15 && b) && bx c (a && d))
        ((p31 && c && d) && !( !a && bx e b)))

theorem shared_factor (p15 p31 p63 a b c d e : Bool) :
    shared p15 p31 p63 a b c d e =
      bx (bx p63 p31)
        (bx (bx (p15 && b && c) (p15 && a && b && d))
          (bx (p31 && c && d)
             (bx (p31 && c && d && !a && e)
                 (p31 && c && d && !a && b)))) := by
  cases p15 <;> cases p31 <;> cases p63 <;> cases a <;> cases b <;>
    cases c <;> cases d <;> cases e <;> decide

-- One coordinate of a rank-one transvection. If v^T u = 0,
-- the readout scalar remains invariant and applying the update twice restores x.
theorem invariant_readout (f : Bool) : bx f (false && f) = f := by
  cases f <;> decide

theorem transvection_inverse (x u f : Bool) :
    bx (bx x (u && f)) (u && bx f (false && f)) = x := by
  cases x <;> cases u <;> cases f <;> decide

-- Boolean discrete integration by parts.
theorem phase_abel (a0 a1 b0 b1 : Bool) :
    bx (a1 && b1) (a0 && b0) =
      bx (a0 && bx b0 b1) (bx a0 a1 && b1) := by
  cases a0 <;> cases a1 <;> cases b0 <;> cases b1 <;> decide

-- The same guarded phase is expressed by its 4 branch values
-- or its finite Möbius differences. This is not normalized Walsh inversion.
theorem selector_mobius (s t f0 f1 f2 f3 : Bool) :
    (if t then (if s then f3 else f2) else (if s then f1 else f0)) =
      bx f0 (bx (s && bx f1 f0)
        (bx (t && bx f2 f0) (s && t && bx (bx f3 f2) (bx f1 f0)))) := by
  cases s <;> cases t <;> cases f0 <;> cases f1 <;>
    cases f2 <;> cases f3 <;> decide
end V55
