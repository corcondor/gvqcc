import Std
namespace V49
def bx (a b : Bool) : Bool := Bool.xor a b

theorem cubic_pullback (t a b c : Bool) :
    (bx t (a && b) && c) = bx (t && c) (a && b && c) := by
  cases t <;> cases a <;> cases b <;> cases c <;> decide

theorem guarded_delta (m t p c : Bool) :
    bx (m && t && c) (m && bx t p && c) = (m && p && c) := by
  cases m <;> cases t <;> cases p <;> cases c <;> decide

theorem target_phase (m t a b : Bool) :
    (m && a && b && t) = (m && (a && b) && t) := by
  cases m <;> cases t <;> cases a <;> cases b <;> decide

theorem abel_step (u v u' v' : Bool) :
    bx (u && v) (u' && v') =
      bx (u && bx v v') (bx u u' && v') := by
  cases u <;> cases v <;> cases u' <;> cases v' <;> decide

theorem debt_cancel (m p t : Bool) :
    bx (m && t) (m && bx t p) = (m && p) := by
  cases m <;> cases p <;> cases t <;> decide

-- The map on a one-dimensional affine fiber is a bijection precisely
-- when the update polynomial is constant on the two fiber points.
def fiber (p0 p1 x : Bool) : Bool := bx x (if x then p1 else p0)
theorem fiber_injective_iff (p0 p1 : Bool) :
    (fiber p0 p1 false ≠ fiber p0 p1 true) ↔ p0 = p1 := by
  cases p0 <;> cases p1 <;> decide

def chi (x : Bool) : Int := if x then -1 else 1
theorem walsh_pair (a b : Bool) :
    2 * chi (a && b) = 1 + chi a + chi b - chi (bx a b) := by
  cases a <;> cases b <;> decide

theorem shared_cubic (a b c d : Bool) :
    bx (a && b && c) (a && b && d) = (a && b && bx c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

-- One Boolean block of Strassen. All additions and subtractions are XOR.
theorem strassen2 (a b c d e f g h : Bool) :
  let p1 := bx a d && bx e h
  let p2 := bx c d && e
  let p3 := a && bx f h
  let p4 := d && bx g e
  let p5 := bx a b && h
  let p6 := bx c a && bx e f
  let p7 := bx b d && bx g h
  bx (bx (bx p1 p4) p5) p7 = bx (a && e) (b && g) ∧
    bx p3 p5 = bx (a && f) (b && h) ∧
    bx p2 p4 = bx (c && e) (d && g) ∧
    bx (bx (bx p1 p2) p3) p6 = bx (c && f) (d && h) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> cases f <;> cases g <;> cases h <;> decide
end V49
