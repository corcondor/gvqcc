import Std.Tactic
namespace GVQCC.Chemistry
def flip (w : BitVec 7) (s t : Bool) : BitVec 7 :=
  (if s then -w else w) + (if t then 64 else 0)
theorem signGauge_delta (w : BitVec 7) (s t : Bool) :
    flip w s t ^^^ w =
      ((if s then (-w) ^^^ w else 0) ^^^ (if t then 64 else 0)) := by
  cases s <;> cases t <;> bv_decide
theorem signGauge_composition (w : BitVec 7) (s t u v : Bool) :
    flip (flip w s t) u v = flip w (Bool.xor s u) (Bool.xor t v) := by
  cases s <;> cases t <;> cases u <;> cases v <;> bv_decide
theorem signGauge_involution (w : BitVec 7) (s t : Bool) :
    flip (flip w s t) s t = w := by
  cases s <;> cases t <;> bv_decide
theorem signGauge_bit0 (w : BitVec 7) (s t : Bool) :
    (flip w s t &&& 1) = (w &&& 1) := by
  cases s <;> cases t <;> bv_decide
end GVQCC.Chemistry
